# Export security rules for Prisma Access SCM 

## How to use
1. Install Poetry if you need.  
https://python-poetry.org/docs/
```
curl -sSL https://install.python-poetry.org | python3 -
```
2. Export security rules
- Poetry
```
poetry install
poetry run python export.py --uid <Service Account ID> --secret <Service Account Secret>  --tsgid <Prisma Access TSG ID>
```
- Python
```
pip install -r requirements.txt
python export.py --uid <Service Account ID> --secret <Service Account Secret>  --tsgid <Prisma Access TSG ID>
```