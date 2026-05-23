export type FieldType = "string" | "number" | "date" | "checkbox";
export type SubmissionStatus = "new" | "in_work" | "rejected" | "done";

export interface Profile {
  id: number;
  user_id: string;
  system: string;
  first_name: string | null;
  last_name: string | null;
  patronymic: string | null;
  username: string | null;
  phone: string | null;
  phone_verified: boolean;
  email: string | null;
  photo_url: string | null;
  language_code: string | null;
  birth_date: string | null;
  study_group: string | null;
  rut_personnel_number: string | null;
  ban_chat: boolean;
  ban_chat_reason: string | null;
  ban_forms: boolean;
  ban_forms_reason: string | null;
  ban_app: boolean;
  ban_app_reason: string | null;
}

export interface FormField {
  id: number;
  label: string;
  type: FieldType;
  regexp: string | null;
  min_value: string | null;
  max_value: string | null;
  default_value: string | null;
  is_active: boolean;
  is_required: boolean;
  order: number;
  profile_key: string | null;
}

export interface FormTemplate {
  id: number;
  name: string;
  description: string | null;
  is_active: boolean;
  order: number;
}

export interface FormTemplateDetailed extends FormTemplate {
  fields: FormField[];
}

export interface StatusHistoryItem {
  id: number;
  from_status: SubmissionStatus | null;
  to_status: SubmissionStatus;
  changed_at: string;
  comment: string | null;
}

export interface Submission {
  id: number;
  form_template_id: number;
  user_id: number;
  values: Record<string, unknown>;
  field_labels: Record<string, string>;
  status: SubmissionStatus;
  created_at: string;
  closed_at: string | null;
  history?: StatusHistoryItem[];
  form_name?: string | null;
}

export interface Faq {
  id: number;
  question: string;
  answer: string;
  question_en: string | null;
  answer_en: string | null;
  is_active: boolean;
  order: number;
}

export interface MonitoringLookup {
  request_number: string;
  status: string | null;
  checked_at: string | null;
  is_subscribed: boolean;
}

export interface MonitoringSubscription {
  request_number: string | null;
  is_active: boolean;
  last_status: string | null;
  checked_at: string | null;
}
