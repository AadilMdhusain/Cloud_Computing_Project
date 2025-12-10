from django.contrib.auth import get_user_model
User = get_user_model()
try:
    if not User.objects.filter(username='admin_ui').exists():
        User.objects.create_user(username='admin_ui', email='admin_ui@example.com', password='password', role='ADMIN')
        print("UI Admin user 'admin_ui' created.")
    else:
        print("UI Admin user 'admin_ui' already exists.")
except Exception as e:
    print(f"Error: {e}")
