// Vite environment variable typing for TypeScript
/// <reference types="vite/client" />

const API_BASE_URL = "https://room-booking-pjo6.onrender.com/api"



// Auth response types
interface LoginResponse {
  access: string
  refresh: string
  user?: any
}

interface RegisterResponse {
  message: string
  user?: any
}

// Room API functions
type Room = {}

export const roomsApi = {
  // Get all rooms with filters
  getRooms: async (filters?: {
    location?: string
    checkIn?: string
    checkOut?: string
    guests?: number
    minPrice?: number
    maxPrice?: number
    roomType?: string
    amenities?: string[]
  }) => {
    const params = new URLSearchParams()

    if (filters?.location) params.append("location", filters.location)
    if (filters?.checkIn) params.append("check_in", filters.checkIn)
    if (filters?.checkOut) params.append("check_out", filters.checkOut)
    if (filters?.guests) params.append("guests", filters.guests.toString())
    if (filters?.minPrice) params.append("min_price", filters.minPrice.toString())
    if (filters?.maxPrice) params.append("max_price", filters.maxPrice.toString())
    if (filters?.roomType) params.append("room_type", filters.roomType)
    if (filters?.amenities) {
      filters.amenities.forEach((amenity) => params.append("amenities", amenity))
    }

    const response = await fetch(`${API_BASE_URL}/rooms?${params}`)
    if (!response.ok) {
      throw new Error("Failed to fetch rooms")
    }
    return response.json()
  },

  // Get single room by ID
  getRoom: async (id: string) => {
    const response = await fetch(`${API_BASE_URL}/rooms/${id}`)
    if (!response.ok) {
      throw new Error("Failed to fetch room")
    }
    return response.json()
  },

  // Create new room (admin only)
  createRoom: async (roomData: Partial<Room>) => {
    const accessToken = localStorage.getItem("access")
    const response = await fetch(`${API_BASE_URL}/rooms`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(roomData),
    })
    if (!response.ok) {
      throw new Error("Failed to create room")
    }
    return response.json()
  },

  // Update room (admin only)
  updateRoom: async (id: string, roomData: Partial<Room>) => {
    const accessToken = localStorage.getItem("access")
    const response = await fetch(`${API_BASE_URL}/rooms/${id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(roomData),
    })
    if (!response.ok) {
      throw new Error("Failed to update room")
    }
    return response.json()
  },

  // Delete room (admin only)
  deleteRoom: async (id: string) => {
    const accessToken = localStorage.getItem("access")
    const response = await fetch(`${API_BASE_URL}/rooms/${id}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    })
    if (!response.ok) {
      throw new Error("Failed to delete room")
    }
    return response.json()
  },
}

// Booking API functions
export const bookingsApi = {
  // Create new booking
  createBooking: async (bookingData: {
    roomId: string
    checkIn: string
    checkOut: string
    guests: number
    guestInfo: {
      name: string
      email: string
      phone: string
    }
  }) => {
    const accessToken = localStorage.getItem("access")
    const response = await fetch(`${API_BASE_URL}/bookings`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(bookingData),
    })
    if (!response.ok) {
      throw new Error("Failed to create booking")
    }
    return response.json()
  },

  // Get all bookings (admin only)
  getBookings: async () => {
    const accessToken = localStorage.getItem("access")
    const response = await fetch(`${API_BASE_URL}/bookings`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    })
    if (!response.ok) {
      throw new Error("Failed to fetch bookings")
    }
    return response.json()
  },

  // Update booking status (admin only)
  updateBookingStatus: async (id: string, status: string) => {
    const accessToken = localStorage.getItem("access")
    const response = await fetch(`${API_BASE_URL}/bookings/${id}/status`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ status }),
    })
    if (!response.ok) {
      throw new Error("Failed to update booking status")
    }
    return response.json()
  },
}

// Auth API functions
export const authApi = {
  // Login
  login: async (credentials: { username: string; password: string }) => {
    const response = await fetch(`${API_BASE_URL}/login/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || "Invalid credentials");
    }

    const data = await response.json();
    const { token } = data; // Adjusted for simple token auth

    if (token) {
      localStorage.setItem("token", token);
    }
    return data;
  },

  // Logout
  logout: () => {
    localStorage.removeItem("token");
  },

  // Fetch user profile
  getUserProfile: async () => {
    const token = localStorage.getItem("token");
    if (!token) throw new Error("No token found");

    const response = await fetch(`${API_BASE_URL}/auth/users/me/`, {
      method: "GET",
      headers: {
        Authorization: `Token ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error("Failed to fetch user profile")
    }

    return response.json()
  },
}

// User authentication functions
export async function login(username: string, password: string): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/jwt/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Login failed');
  }
  return response.json();
}

export async function register(data: {
  username: string;
  email: string;
  mobile_no: string;
  password: string;
  confirm_password: string;
}): Promise<RegisterResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/register/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Registration failed');
  }
  return response.json();
}

export async function logout(): Promise<void> {
  const refresh = localStorage.getItem("refresh");
  if (refresh) {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/logout/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      });
      if (!response.ok) {
        console.warn('Logout API call failed');
      }
    } catch (error) {
      console.warn('Logout API call failed:', error);
    }
  }
  // Always clear local storage regardless of API call success
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  localStorage.removeItem("user");
}

// Upload API functions
export const uploadApi = {
  // Upload room images
  uploadImages: async (files: FileList) => {
    const formData = new FormData()
    Array.from(files).forEach((file) => {
      formData.append("images", file)
    })

    const accessToken = localStorage.getItem("access")
    const response = await fetch(`${API_BASE_URL}/upload/images`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      body: formData,
    })
    if (!response.ok) {
      throw new Error("Failed to upload images")
    }
    return response.json()
  },
}
