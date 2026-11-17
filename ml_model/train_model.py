
import os
import joblib
import numpy as np

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score

# Reproducible sample data for demo
np.random.seed(42)

n = 500
attendance = np.random.uniform(30, 100, n)
previous_marks = np.random.uniform(20, 100, n)
assessment_average = np.random.uniform(20, 100, n)

# Synthetic target: expected future marks
noise = np.random.normal(0, 5, n)
future_marks = np.clip(
    0.40 * previous_marks
    + 0.35 * assessment_average
    + 0.25 * attendance
    + noise,
    0, 100
)

# Demo risk labels based on academic indicators
risk = np.where(
    (attendance < 60) | (future_marks < 40),
    "High Risk",
    np.where(
        (attendance < 75) | (future_marks < 55),
        "Medium Risk",
        "Low Risk"
    )
)

X = np.column_stack([
    attendance,
    previous_marks,
    assessment_average
])

X_train, X_test, y_train, y_test = train_test_split(
    X, future_marks, test_size=0.2, random_state=42
)

_, _, risk_train, risk_test = train_test_split(
    X, risk, test_size=0.2, random_state=42
)

performance_model = RandomForestRegressor(
    n_estimators=100, random_state=42
)
performance_model.fit(X_train, y_train)

risk_model = RandomForestClassifier(
    n_estimators=100, random_state=42
)
risk_model.fit(X_train, risk_train)

predictions = performance_model.predict(X_test)

os.makedirs("ml_model", exist_ok=True)

joblib.dump(
    performance_model,
    "ml_model/performance_model.pkl"
)
joblib.dump(
    risk_model,
    "ml_model/risk_model.pkl"
)

print("AI/ML models trained successfully!")
print("Performance MAE:", round(
    mean_absolute_error(y_test, predictions), 2
))
print("Risk model accuracy:", round(
    accuracy_score(risk_test, risk_model.predict(X_test)) * 100, 2
), "%")
print("Models saved in ml_model folder.")
