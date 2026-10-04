import io
import base64
import os
import pickle
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Count

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

from core.models import Employee
from core.decorators import hr_staff_required


@login_required
@hr_staff_required
def forecast_index(request):
    today = datetime.now()

    monthly_counts = (
        Employee.objects
        .filter(date_hired__isnull=False)
        .values('date_hired__year', 'date_hired__month')
        .annotate(count=Count('id'))
        .order_by('date_hired__year', 'date_hired__month')
    )

    months = []
    counts = []
    for entry in monthly_counts:
        year = entry['date_hired__year']
        month = entry['date_hired__month']
        label = f"{year}-{month:02d}"
        months.append(label)
        counts.append(entry['count'])

    if not months:
        context = {'no_data': True}
        return render(request, 'forecast/index.html', context)

    cumulative_counts = []
    running_total = 0
    for c in counts:
        running_total += c
        cumulative_counts.append(running_total)

    X = np.array(range(1, len(cumulative_counts) + 1)).reshape(-1, 1)
    y = np.array(cumulative_counts)

    model = LinearRegression()
    model.fit(X, y)

    future_months_count = 3
    last_month_num = len(cumulative_counts)
    future_X = np.array(range(last_month_num + 1, last_month_num + future_months_count + 1)).reshape(-1, 1)
    forecast = model.predict(future_X)

    y_pred = model.predict(X)
    mse = mean_squared_error(y, y_pred)
    r2 = r2_score(y, y_pred)

    forecast_months = []
    last_dt = datetime.strptime(months[-1], '%Y-%m')
    for i in range(1, future_months_count + 1):
        next_month = last_dt.month + i
        next_year = last_dt.year
        while next_month > 12:
            next_month -= 12
            next_year += 1
        forecast_months.append(f"{next_year}-{next_month:02d}")

    model_dir = os.path.join(settings.MEDIA_ROOT, 'forecast')
    os.makedirs(model_dir, exist_ok=True)

    model_filename = os.path.join(model_dir, 'employee_model.pkl')
    with open(model_filename, 'wb') as f:
        pickle.dump(model, f)

    forecast_df = pd.DataFrame({
        'Month': forecast_months,
        'Forecasted_Employee_Count': np.round(forecast, 2)
    })
    csv_path = os.path.join(model_dir, 'employee_forecast.csv')
    forecast_df.to_csv(csv_path, index=False)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(X, y, color='blue', label='Actual Data')
    ax.plot(X, model.predict(X), color='red', label='Regression Line')
    ax.scatter(future_X, forecast, color='green', label='Forecasted Values', marker='x', s=100)
    ax.set_title('Employee Forecasting using Linear Regression')
    ax.set_xlabel('Month Index')
    ax.set_ylabel('Number of Employees')
    ax.legend()
    ax.grid(True)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    chart_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    forecast_list = list(zip(forecast_months, np.round(forecast, 2)))
    historical_data = list(zip(months, cumulative_counts))

    context = {
        'no_data': False,
        'chart': chart_base64,
        'historical_data': historical_data,
        'forecast_data': forecast_list,
        'intercept': round(model.intercept_, 2),
        'coefficient': round(model.coef_[0], 2),
        'mse': round(mse, 2),
        'r2': round(r2, 2),
        'total_months': len(months),
        'total_employees': cumulative_counts[-1] if cumulative_counts else 0,
        'forecast_months_count': future_months_count,
    }

    return render(request, 'forecast/index.html', context)
