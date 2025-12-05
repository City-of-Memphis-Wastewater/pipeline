# Send a curl request to use MockData with the Eds Trend HTML
```
poetry run eds gui
# then from another terminal (or the same, after server starts)
curl -X POST http://127.0.0.1:8082/api/fetch_eds_trend \
  -H "Content-Type: application/json" \
  -d '{"idcs":["M100FI"],"use_mock":true}'
```