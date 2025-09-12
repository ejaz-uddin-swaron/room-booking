# VillaEase Backend API Documentation

## Overview
This document outlines the complete API specification for the VillaEase room booking platform. The frontend expects a RESTful API with JSON responses and JWT-based authentication for admin operations.

## Base Configuration

### Base URL
\`\`\`
http://localhost:3001/api
\`\`\`

### Headers
- **Content-Type**: `application/json`
- **Authorization**: `Bearer <jwt_token>` (for protected routes)

### Response Format
All API responses should follow this structure:
\`\`\`json
{
  "success": true,
  "data": {},
  "message": "Optional message"
}
\`\`\`

### Error Response Format
\`\`\`json
{
  "success": false,
  "error": "Error message",
  "status": 400
}
\`\`\`

## Authentication

### Admin Login
**POST** `/auth/login`

**Request Body:**
\`\`\`json
{
  "username": "admin",
  "password": "admin123"
}
\`\`\`

**Response:**
\`\`\`json
{
  "success": true,
  "data": {
    "token": "jwt_token_here",
    "user": {
      "id": "admin_id",
      "username": "admin",
      "role": "admin"
    }
  }
}
\`\`\`

### Verify Token
**GET** `/auth/verify`

**Headers:**
\`\`\`
Authorization: Bearer <jwt_token>
\`\`\`

**Response:**
\`\`\`json
{
  "success": true,
  "data": {
    "valid": true,
    "user": {
      "id": "admin_id",
      "username": "admin",
      "role": "admin"
    }
  }
}
\`\`\`

## Rooms API

### Get All Rooms
**GET** `/rooms`

**Query Parameters:**
- `location` (string, optional): Filter by location
- `check_in` (string, optional): Check-in date (YYYY-MM-DD)
- `check_out` (string, optional): Check-out date (YYYY-MM-DD)
- `guests` (number, optional): Number of guests
- `min_price` (number, optional): Minimum price per night
- `max_price` (number, optional): Maximum price per night
- `room_type` (string, optional): Room type filter
- `amenities` (array, optional): Array of amenity names

**Example Request:**
\`\`\`
GET /api/rooms?location=London&guests=2&min_price=100&max_price=300&amenities=WiFi&amenities=Pool
\`\`\`

**Response:**
\`\`\`json
{
  "success": true,
  "data": [
    {
      "id": "room_1",
      "name": "Luxury Ocean View Suite",
      "type": "Suite",
      "price": 250,
      "rating": 4.8,
      "reviews": 124,
      "images": [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg"
      ],
      "amenities": ["WiFi", "Pool", "Gym", "Spa"],
      "description": "Beautiful ocean view suite with modern amenities",
      "location": "London",
      "maxGuests": 4,
      "bedrooms": 2,
      "bathrooms": 2,
      "size": 85,
      "available": true,
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T00:00:00Z"
    }
  ]
}
\`\`\`

### Get Single Room
**GET** `/rooms/:id`

**Response:**
\`\`\`json
{
  "success": true,
  "data": {
    "id": "room_1",
    "name": "Luxury Ocean View Suite",
    "type": "Suite",
    "price": 250,
    "rating": 4.8,
    "reviews": 124,
    "images": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg"
    ],
    "amenities": ["WiFi", "Pool", "Gym", "Spa"],
    "description": "Beautiful ocean view suite with modern amenities",
    "location": "London",
    "maxGuests": 4,
    "bedrooms": 2,
    "bathrooms": 2,
    "size": 85,
    "available": true,
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z"
  }
}
\`\`\`

### Create Room (Admin Only)
**POST** `/rooms`

**Headers:**
\`\`\`
Authorization: Bearer <jwt_token>
Content-Type: application/json
\`\`\`

**Request Body:**
\`\`\`json
{
  "name": "New Room Name",
  "type": "Suite",
  "price": 200,
  "images": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg"
  ],
  "amenities": ["WiFi", "Pool"],
  "description": "Room description",
  "location": "Paris",
  "maxGuests": 2,
  "bedrooms": 1,
  "bathrooms": 1,
  "size": 45,
  "available": true
}
\`\`\`

**Response:**
\`\`\`json
{
  "success": true,
  "data": {
    "id": "new_room_id",
    "name": "New Room Name",
    "type": "Suite",
    "price": 200,
    "rating": 0,
    "reviews": 0,
    "images": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg"
    ],
    "amenities": ["WiFi", "Pool"],
    "description": "Room description",
    "location": "Paris",
    "maxGuests": 2,
    "bedrooms": 1,
    "bathrooms": 1,
    "size": 45,
    "available": true,
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z"
  }
}
\`\`\`

### Update Room (Admin Only)
**PUT** `/rooms/:id`

**Headers:**
\`\`\`
Authorization: Bearer <jwt_token>
Content-Type: application/json
\`\`\`

**Request Body:** (Same as Create Room, all fields optional)
\`\`\`json
{
  "name": "Updated Room Name",
  "price": 300,
  "available": false
}
\`\`\`

**Response:** (Same as Create Room response)

### Delete Room (Admin Only)
**DELETE** `/rooms/:id`

**Headers:**
\`\`\`
Authorization: Bearer <jwt_token>
\`\`\`

**Response:**
\`\`\`json
{
  "success": true,
  "message": "Room deleted successfully"
}
\`\`\`

## Bookings API

### Create Booking
**POST** `/bookings`

**Request Body:**
\`\`\`json
{
  "roomId": "room_1",
  "checkIn": "2024-02-01",
  "checkOut": "2024-02-05",
  "guests": 2,
  "guestInfo": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890"
  }
}
\`\`\`

**Response:**
\`\`\`json
{
  "success": true,
  "data": {
    "id": "booking_1",
    "roomId": "room_1",
    "checkIn": "2024-02-01",
    "checkOut": "2024-02-05",
    "guests": 2,
    "totalPrice": 1000,
    "status": "pending",
    "guestInfo": {
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+1234567890"
    },
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z"
  }
}
\`\`\`

### Get All Bookings (Admin Only)
**GET** `/bookings`

**Headers:**
\`\`\`
Authorization: Bearer <jwt_token>
\`\`\`

**Response:**
\`\`\`json
{
  "success": true,
  "data": [
    {
      "id": "booking_1",
      "roomId": "room_1",
      "checkIn": "2024-02-01",
      "checkOut": "2024-02-05",
      "guests": 2,
      "totalPrice": 1000,
      "status": "confirmed",
      "guestInfo": {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890"
      },
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T00:00:00Z",
      "room": {
        "id": "room_1",
        "name": "Luxury Ocean View Suite",
        "location": "London"
      }
    }
  ]
}
\`\`\`

### Update Booking Status (Admin Only)
**PATCH** `/bookings/:id/status`

**Headers:**
\`\`\`
Authorization: Bearer <jwt_token>
Content-Type: application/json
\`\`\`

**Request Body:**
\`\`\`json
{
  "status": "confirmed"
}
\`\`\`

**Valid Status Values:**
- `pending`
- `confirmed`
- `cancelled`
- `completed`

**Response:**
\`\`\`json
{
  "success": true,
  "data": {
    "id": "booking_1",
    "status": "confirmed",
    "updatedAt": "2024-01-01T00:00:00Z"
  }
}
\`\`\`

## File Upload API

### Upload Images
**POST** `/upload/images`

**Headers:**
\`\`\`
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data
\`\`\`

**Request Body:**
- Form data with `images` field containing multiple files
- Maximum file size: 5MB per file
- Supported formats: JPG, PNG, WebP

**Response:**
\`\`\`json
{
  "success": true,
  "data": {
    "urls": [
      "https://yourdomain.com/uploads/image1.jpg",
      "https://yourdomain.com/uploads/image2.jpg"
    ]
  }
}
\`\`\`

## Admin Statistics API

### Get Dashboard Stats (Admin Only)
**GET** `/admin/stats`

**Headers:**
\`\`\`
Authorization: Bearer <jwt_token>
\`\`\`

**Response:**
\`\`\`json
{
  "success": true,
  "data": {
    "totalRooms": 25,
    "totalBookings": 150,
    "totalRevenue": 45000,
    "occupancyRate": 75.5
  }
}
\`\`\`

## Database Schema Requirements

### Rooms Table
\`\`\`sql
CREATE TABLE rooms (
  id VARCHAR(255) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  type VARCHAR(100) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  rating DECIMAL(2,1) DEFAULT 0,
  reviews INT DEFAULT 0,
  images JSON, -- Array of image URLs
  amenities JSON, -- Array of amenity names
  description TEXT,
  location VARCHAR(255) NOT NULL,
  max_guests INT NOT NULL,
  bedrooms INT NOT NULL,
  bathrooms INT NOT NULL,
  size INT NOT NULL, -- Square meters
  available BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
\`\`\`

### Bookings Table
\`\`\`sql
CREATE TABLE bookings (
  id VARCHAR(255) PRIMARY KEY,
  room_id VARCHAR(255) NOT NULL,
  check_in DATE NOT NULL,
  check_out DATE NOT NULL,
  guests INT NOT NULL,
  total_price DECIMAL(10,2) NOT NULL,
  status ENUM('pending', 'confirmed', 'cancelled', 'completed') DEFAULT 'pending',
  guest_info JSON, -- {name, email, phone}
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (room_id) REFERENCES rooms(id)
);
\`\`\`

### Admin Users Table
\`\`\`sql
CREATE TABLE admin_users (
  id VARCHAR(255) PRIMARY KEY,
  username VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL, -- Hashed password
  role VARCHAR(50) DEFAULT 'admin',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
\`\`\`

## Environment Variables

### Required Environment Variables
\`\`\`env
# Database
DATABASE_URL=your_database_connection_string

# JWT
JWT_SECRET=your_super_secret_jwt_key
JWT_EXPIRES_IN=24h

# Server
PORT=3001
NODE_ENV=development

# CORS
CORS_ORIGIN=http://localhost:3000

# File Upload
UPLOAD_DIR=uploads
MAX_FILE_SIZE=5242880
ALLOWED_FILE_TYPES=jpg,jpeg,png,webp

# Admin Credentials (for seeding)
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123
\`\`\`

## CORS Configuration

Enable CORS for the frontend domain:
\`\`\`javascript
app.use(cors({
  origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
  credentials: true
}));
\`\`\`

## Error Handling

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

### Error Response Examples
\`\`\`json
{
  "success": false,
  "error": "Room not found",
  "status": 404
}
\`\`\`

\`\`\`json
{
  "success": false,
  "error": "Validation failed",
  "status": 422,
  "details": {
    "name": "Name is required",
    "price": "Price must be a positive number"
  }
}
\`\`\`

## Security Requirements

1. **JWT Authentication**: Use JWT tokens for admin authentication
2. **Password Hashing**: Hash admin passwords using bcrypt
3. **Input Validation**: Validate all input data
4. **SQL Injection Prevention**: Use parameterized queries
5. **File Upload Security**: Validate file types and sizes
6. **Rate Limiting**: Implement rate limiting for API endpoints

## Testing Endpoints

Use these sample data for testing:

### Sample Room Data
\`\`\`json
{
  "name": "Luxury Ocean View Suite",
  "type": "Suite",
  "price": 250,
  "images": [
    "https://images.unsplash.com/photo-1566073771259-6a8506099945",
    "https://images.unsplash.com/photo-1564013799919-ab600027ffc6"
  ],
  "amenities": ["WiFi", "Pool", "Gym", "Spa", "Balcony"],
  "description": "Beautiful ocean view suite with modern amenities and stunning sunset views.",
  "location": "London",
  "maxGuests": 4,
  "bedrooms": 2,
  "bathrooms": 2,
  "size": 85,
  "available": true
}
\`\`\`

### Sample Booking Data
\`\`\`json
{
  "roomId": "room_1",
  "checkIn": "2024-02-01",
  "checkOut": "2024-02-05",
  "guests": 2,
  "guestInfo": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890"
  }
}
\`\`\`

## Notes for Backend Developer

1. **Price Calculation**: The frontend expects `totalPrice` to be calculated on the backend based on room price and number of nights
2. **Date Validation**: Ensure check-in date is before check-out date and both are in the future
3. **Availability Check**: Verify room availability for the requested dates before creating bookings
4. **Image URLs**: Return full URLs for images, not relative paths
5. **Pagination**: Consider implementing pagination for rooms and bookings if the dataset grows large
6. **Search Optimization**: Implement efficient database queries for room filtering
7. **Booking Conflicts**: Prevent double bookings for the same room and dates

This API specification provides everything needed to build a fully functional backend for the VillaEase booking platform.
