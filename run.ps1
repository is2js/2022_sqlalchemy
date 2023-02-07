# development / testing / production / default
$env:APP_CONFIG='development'
$env:FLASK_APP='manage.py'

$env:FLASK_ENV=$env:APP_CONFIG
$env:FLASK_RUN_HOST='localhost'
$env:FLASK_RUN_PORT='5000'

./venv/Scripts/activate