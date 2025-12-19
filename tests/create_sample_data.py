import pandas as pd
from pathlib import Path

def create_sample_sales_data():
    """Create sample sales CSV"""
    data = pd.DataFrame({
        'order_id': range(1, 101),
        'product': ['Product A', 'Product B', 'Product C'] * 33 + ['Product A'],
        'quantity': [i % 10 + 1 for i in range(100)],
        'price': [10.99, 25.50, 15.75] * 33 + [10.99],
        'order_date': pd.date_range('2025-01-01', periods=100, freq='H')
    })
    
    output_path = Path('../data/raw/sales_data.csv')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output_path, index=False)
    print(f"✓ Created {output_path}")

def create_sample_customer_data():
    """Create sample customer CSV"""
    data = pd.DataFrame({
        'customer_id': range(1, 51),
        'name': [f'Customer {i}' for i in range(1, 51)],
        'email': [f'customer{i}@example.com' for i in range(1, 51)],
        'signup_date': pd.date_range('2024-01-01', periods=50, freq='W'),
        'total_purchases': [i * 100 for i in range(1, 51)]
    })
    
    output_path = Path('../data/raw/customers.csv')
    data.to_csv(output_path, index=False)
    print(f"✓ Created {output_path}")

if __name__ == "__main__":
    create_sample_sales_data()
    create_sample_customer_data()
    print("\n✓ Sample data created successfully!")