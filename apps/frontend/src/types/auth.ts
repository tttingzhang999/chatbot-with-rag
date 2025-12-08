export type User = {
  id: string;
  username: string;
  email: string;
  created_at?: string;
}

export type LoginRequest = {
  username: string;
  password: string;
}

export type RegisterRequest = {
  username: string;
  email: string;
  password: string;
}

export type TokenResponse = {
  access_token: string;
  token_type: string;
  user_id: string;
  username: string;
  email: string;
}
