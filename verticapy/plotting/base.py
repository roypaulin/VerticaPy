"""
(c)  Copyright  [2018-2023]  OpenText  or one of its
affiliates.  Licensed  under  the   Apache  License,
Version 2.0 (the  "License"); You  may  not use this
file except in compliance with the License.

You may obtain a copy of the License at:
http://www.apache.org/licenses/LICENSE-2.0

Unless  required  by applicable  law or  agreed to in
writing, software  distributed  under the  License is
distributed on an  "AS IS" BASIS,  WITHOUT WARRANTIES
OR CONDITIONS OF ANY KIND, either express or implied.
See the  License for the specific  language governing
permissions and limitations under the License.
"""
import math
from typing import TYPE_CHECKING

import verticapy._config.config as conf
from verticapy._typing import ArrayLike
from verticapy._utils._sql._cast import to_varchar
from verticapy._utils._sql._format import quote_ident
from verticapy._utils._sql._sys import _executeSQL
from verticapy.errors import ParameterError

if TYPE_CHECKING:
    from verticapy.core.vdataframe.base import vDataFrame

if conf._get_import_success("dateutil"):
    from dateutil.parser import parse


class PlottingBase:
    @property
    def _markers(self):
        return ["^", "o", "+", "*", "h", "x", "D", "1"]

    @staticmethod
    def compute_plot_variables(
        vdf: "vDataFrame",
        method: str = "density",
        of: str = "",
        max_cardinality: int = 6,
        nbins: int = 0,
        h: float = 0.0,
        pie: bool = False,
    ) -> tuple[ArrayLike, ArrayLike, ArrayLike, float, bool]:
        """
	    Computes the aggregations needed to draw a 1D graphic 
	    using the Matplotlib API.
	    """
        other_columns = ""
        if method.lower() == "median":
            method = "50%"
        elif method.lower() == "mean":
            method = "avg"
        if (
            method.lower() not in ["avg", "min", "max", "sum", "density", "count"]
            and "%" != method[-1]
        ) and of:
            raise ParameterError(
                "Parameter 'of' must be empty when using customized aggregations."
            )
        if (
            (method.lower() in ["avg", "min", "max", "sum"])
            or (method.lower() and method[-1] == "%")
        ) and (of):
            if method.lower() in ["avg", "min", "max", "sum"]:
                aggregate = f"{method.upper()}({quote_ident(of)})"
            elif method and method[-1] == "%":
                aggregate = f"""
	                APPROXIMATE_PERCENTILE({quote_ident(of)} 
	                                       USING PARAMETERS
	                                       percentile = {float(method[0:-1]) / 100})"""
            else:
                raise ParameterError(
                    "The parameter 'method' must be in [avg|mean|min|max|sum|median|q%]"
                    f" or a customized aggregation. Found {method}."
                )
        elif method.lower() in ["density", "count"]:
            aggregate = "count(*)"
        elif isinstance(method, str):
            aggregate = method
            other_columns = ", " + ", ".join(
                vdf._parent.get_columns(exclude_columns=[vdf._alias])
            )
        else:
            raise ParameterError(
                "The parameter 'method' must be in [avg|mean|min|max|sum|median|q%]"
                f" or a customized aggregation. Found {method}."
            )
        # depending on the cardinality, the type, the vDataColumn can be treated as categorical or not
        cardinality, count, is_numeric, is_date, is_categorical = (
            vdf.nunique(True),
            vdf._parent.shape()[0],
            vdf.isnum() and not (vdf.isbool()),
            (vdf.category() == "date"),
            False,
        )
        rotation = 0 if ((is_numeric) and (cardinality > max_cardinality)) else 90
        # case when categorical
        if (((cardinality <= max_cardinality) or not (is_numeric)) or pie) and not (
            is_date
        ):
            if (is_numeric) and not (pie):
                query = f"""
	                SELECT 
	                    {vdf._alias},
	                    {aggregate}
	                FROM {vdf._parent._genSQL()} 
	                WHERE {vdf._alias} IS NOT NULL 
	                GROUP BY {vdf._alias} 
	                ORDER BY {vdf._alias} ASC 
	                LIMIT {max_cardinality}"""
            else:
                table = vdf._parent._genSQL()
                if (pie) and (is_numeric):
                    enum_trans = (
                        vdf.discretize(h=h, return_enum_trans=True)[0].replace(
                            "{}", vdf._alias
                        )
                        + " AS "
                        + vdf._alias
                    )
                    if of:
                        enum_trans += f" , {of}"
                    table = (
                        f"(SELECT {enum_trans + other_columns} FROM {table}) enum_table"
                    )
                cast_alias = to_varchar(vdf.category(), vdf._alias)
                query = f"""
	                (SELECT 
	                    /*+LABEL('plotting._matplotlib.compute_plot_variables')*/ 
	                    {cast_alias} AS {vdf._alias},
	                    {aggregate}
	                 FROM {table} 
	                 GROUP BY {cast_alias} 
	                 ORDER BY 2 DESC 
	                 LIMIT {max_cardinality})"""
                if cardinality > max_cardinality:
                    query += f"""
	                    UNION 
	                    (SELECT 
	                        'Others',
	                        {aggregate} 
	                     FROM {table}
	                     WHERE {vdf._alias} NOT IN
	                     (SELECT 
	                        {vdf._alias} 
	                      FROM {table}
	                      GROUP BY {vdf._alias}
	                      ORDER BY {aggregate} DESC
	                      LIMIT {max_cardinality}))"""
            query_result = _executeSQL(
                query=query, title="Computing the histogram heights", method="fetchall"
            )
            if query_result[-1][1] == None:
                del query_result[-1]
            z = [item[0] for item in query_result]
            y = (
                [
                    item[1] / float(count) if item[1] != None else 0
                    for item in query_result
                ]
                if (method.lower() == "density")
                else [item[1] if item[1] != None else 0 for item in query_result]
            )
            x = [0.4 * i + 0.2 for i in range(0, len(y))]
            h = 0.39
            is_categorical = True
        # case when date
        elif is_date:
            if (h <= 0) and (nbins <= 0):
                h = vdf.numh()
            elif nbins > 0:
                query_result = _executeSQL(
                    query=f"""
	                    SELECT 
	                        /*+LABEL('plotting._matplotlib.compute_plot_variables')*/
	                        DATEDIFF('second', MIN({vdf._alias}), MAX({vdf._alias}))
	                    FROM {vdf._parent._genSQL()}""",
                    title="Computing the histogram interval",
                    method="fetchrow",
                )
                h = float(query_result[0]) / nbins
            min_date = vdf.min()
            converted_date = f"DATEDIFF('second', '{min_date}', {vdf._alias})"
            query_result = _executeSQL(
                query=f"""
	                SELECT 
	                    /*+LABEL('plotting._matplotlib.compute_plot_variables')*/
	                    FLOOR({converted_date} / {h}) * {h}, 
	                    {aggregate} 
	                FROM {vdf._parent._genSQL()}
	                WHERE {vdf._alias} IS NOT NULL 
	                GROUP BY 1 
	                ORDER BY 1""",
                title="Computing the histogram heights",
                method="fetchall",
            )
            x = [float(item[0]) for item in query_result]
            y = (
                [item[1] / float(count) for item in query_result]
                if (method.lower() == "density")
                else [item[1] for item in query_result]
            )
            query = "("
            for idx, item in enumerate(query_result):
                query_tmp = f"""
	                (SELECT 
	                    {{}}
	                    TIMESTAMPADD('second',
	                                 {math.floor(h * idx)},
	                                 '{min_date}'::timestamp))"""
                if idx == 0:
                    query += query_tmp.format(
                        "/*+LABEL('plotting._matplotlib.compute_plot_variables')*/"
                    )
                else:
                    query += f" UNION {query_tmp.format('')}"
            query += ")"
            h = 0.94 * h
            query_result = _executeSQL(
                query, title="Computing the datetime intervals.", method="fetchall"
            )
            z = [item[0] for item in query_result]
            z.sort()
            is_categorical = True
        # case when numerical
        else:
            if (h <= 0) and (nbins <= 0):
                h = vdf.numh()
            elif nbins > 0:
                h = float(vdf.max() - vdf.min()) / nbins
            if (vdf.ctype == "int") or (h == 0):
                h = max(1.0, h)
            query_result = _executeSQL(
                query=f"""
	                SELECT
	                    /*+LABEL('plotting._matplotlib.compute_plot_variables')*/
	                    FLOOR({vdf._alias} / {h}) * {h},
	                    {aggregate} 
	                FROM {vdf._parent._genSQL()}
	                WHERE {vdf._alias} IS NOT NULL
	                GROUP BY 1
	                ORDER BY 1""",
                title="Computing the histogram heights",
                method="fetchall",
            )
            y = (
                [item[1] / float(count) for item in query_result]
                if (method.lower() == "density")
                else [item[1] for item in query_result]
            )
            x = [float(item[0]) + h / 2 for item in query_result]
            h = 0.94 * h
            z = None
        return [x, y, z, h, is_categorical]

    @staticmethod
    def parse_datetime(D: list) -> list:
        """
	    Parses the list and casts the value to the datetime
	    format if possible.
	    """
        try:
            return [parse(d) for d in D]
        except:
            return copy.deepcopy(D)

    @staticmethod
    def updated_dict(d1: dict, d2: dict, color_idx: int = 0,) -> dict:
        """
	    Updates the input dictionary using another one.
	    """
        d = {}
        for elem in d1:
            d[elem] = d1[elem]
        for elem in d2:
            if elem == "color":
                if isinstance(d2["color"], str):
                    d["color"] = d2["color"]
                elif color_idx < 0:
                    d["color"] = [elem for elem in d2["color"]]
                else:
                    d["color"] = d2["color"][color_idx % len(d2["color"])]
            else:
                d[elem] = d2[elem]
        return d
