from datetime import datetime

def generate_batch_id(fruit: str, count: int):
    date = datetime.utcnow().strftime("%Y%m%d")
    return f"BATCH-{fruit[:3].upper()}-{date}-{str(count).zfill(3)}"
