# Login API Documentation

## Endpoint
**POST** `/auth/login`

## Request Body
```json
{
  "username": "exampleuser",
  "password": "password123"
}
```

## Response Example
```json
{
  "success": true,
  "data": {
    "token": "<access_token>",
    "refresh": "<refresh_token>",
    "user": {
      "id": 1,
      "username": "exampleuser",
      "role": "client"
    }
  }
}
```

## Notes
- The `username` and `password` fields are required.
- The `Authorization` header is not needed for this endpoint.
- Tokens (`access` and `refresh`) will be returned upon successful login.
