from fia_agent.models import TableDefinition, ColumnDefinition
from fia_agent.services.text2sql import Text2SQLTranslator
import asyncio

schema = [
    TableDefinition(
        name="financials_quarterly",
        columns=[ColumnDefinition(name="segment", type="STRING"), ColumnDefinition(name="revenue_usd", type="FLOAT")],
    )
]


def test_fallback_generation():
    translator = Text2SQLTranslator()
    sql, rationale = asyncio.run(translator.generate_sql("Show revenue by segment", schema, None))
    assert "SELECT" in sql
    assert "segment" in sql.lower()
    assert "Target table" in rationale
