from website import create_app
from website.models import CustomEncoder

app = create_app()
app.json_encoder = CustomEncoder

if __name__ == '__main__':
  app.run(debug=True)
