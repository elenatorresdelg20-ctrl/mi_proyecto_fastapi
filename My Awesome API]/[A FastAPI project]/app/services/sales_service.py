import pandas as pd
from io import StringIO

def process_sales_csv(tenant_code: str, file):
    content = file.file.read().decode("utf-8")
    df = pd.read_csv(StringIO(content))
    total = len(df)
    first = df.iloc[0]
    return {
        "id": total,
        "tenant_id": 1,
        "date": first["date"],
        "product": first["product"],
        "amount": first["amount"],
        "channel": first.get("channel", "Upload"),
    }
