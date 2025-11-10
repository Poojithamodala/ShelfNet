# ShelfNet: Dynamic Shelf Life Modeling for Fruits and Vegetables

ShelfNet is an end-to-end system that preprocesses IoT sensor data, trains an LSTM model to predict remaining shelf life, evaluates model quality, and serves a Flask web dashboard to upload CSV/Excel data and visualize predictions and alerts.

## Features
- Data preprocessing: timestamp parsing, cleaning, scaling, categorical encoding, and sequence building
- LSTM regression for remaining shelf life prediction
- Evaluation: RMSE and R², plus diagnostic plots
- Flask dashboard: CSV/Excel upload, charts, insights, and alerts when shelf life is below a threshold
- Modular codebase with CLI scripts for training and prediction

## Expected Dataset Schema
CSV or Excel (.xlsx) with columns (Excel example):
- `EntryID`
- `Fruit`
- `Timestamp (Day_1, Day_2, ...)` or `Time_Step(0,1,2,...)`
- `Temperature(°C)`, `Humidity(%)`, `Ethylene(ppm)`, `CO2(ppm)`, `O2_Level(%)`, `Light_Intensity(lux)`, `Vibration_Level(m/s^2)`
- `Storage_Door_Open_Count`
- `Power_Supply_Status` (Fluctuation/Normal)

Notes:
- `remaining_shelf_life` is auto-generated at load time if absent as: `max(Time_Step) - Time_Step` per `Fruit` group.
- Columns are normalized internally (e.g., spaces/symbols removed) and mapped to features.

## Quickstart
1. Create a virtual environment and install dependencies:
```bash
pip install -r requirements.txt
```

2. Train the model (artifacts are saved under `artifacts/`):
```bash
python -m shelfnet.train --data shelfnet/data/fruits_shelf_life.xlsx --lookback 24 --batch-size 64 --epochs 30
```

3. Batch predict on new data:
```bash
python -m shelfnet.predict --data shelfnet/data/fruits_shelf_life.xlsx --out predictions.csv --threshold 24
```

4. Run the dashboard:
```bash
export FLASK_APP=shelfnet.app:app
flask run
```
On Windows PowerShell:
```powershell
$env:FLASK_APP = "shelfnet.app:app"
flask run
```

Open http://127.0.0.1:5000/

## Notes
- Training and inference accept `.csv` or `.xlsx`.
- If your target column already exists under a different name, pass it with `--target-col`.
- If `Time_Step` is missing but a day label like `Day_1` exists, it will be parsed automatically.
- For sensors not present in your dataset, they are simply ignored; present sensors are scaled/encoded.

## Project Structure
```
ShelfNet/
  README.md
  requirements.txt
  shelfnet/
    __init__.py
    data.py
    model.py
    evaluate.py
    train.py
    predict.py
    visualization.py
    app.py
  templates/
    base.html
    index.html
  static/
    css/
      style.css
  artifacts/
    (saved models and scalers)
```
