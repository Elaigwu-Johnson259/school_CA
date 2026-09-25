export interface School {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  address: string | null;
  state: string | null;
  country: string | null;
  motto: string | null;
  website: string | null;
  principal_name: string | null;
  primary_color: string | null;
  secondary_color: string | null;
  is_active: boolean;
  logo_path: string | null;
  signature_path: string | null;
  stamp_path: string | null;
  created_at: string;
  updated_at: string;
}
