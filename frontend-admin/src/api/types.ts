export type System = "max" | "beavers";
export type AdminRole = "employee" | "admin";
export type FieldType = "string" | "number" | "date" | "checkbox";
export type SubmissionStatus = "new" | "in_work" | "rejected" | "done";

export interface AdminProfile {
  id: number;
  max_user_id: string;
  full_name: string;
  role: AdminRole;
  is_active: boolean;
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
  meta: Record<string, unknown> | null;
}

export interface FormTemplate {
  id: number;
  name: string;
  description: string | null;
  is_active: boolean;
  order: number;
  reply_on_accept: string | null;
  created_at: string;
  updated_at: string;
}

export interface FormTemplateDetailed extends FormTemplate {
  fields: FormField[];
}

export interface Submitter {
  id: number;
  first_name: string | null;
  last_name: string | null;
  patronymic: string | null;
  username: string | null;
  photo_url: string | null;
  user_id: string | null;
  system: string | null;
  birth_date: string | null;
  study_group: string | null;
  phone: string | null;
  phone_verified: boolean;
  email: string | null;
}

export interface StatusHistoryItem {
  id: number;
  from_status: SubmissionStatus | null;
  to_status: SubmissionStatus;
  changed_by: number | null;
  changed_at: string;
  comment: string | null;
}

export interface Submission {
  id: number;
  form_template_id: number;
  user_id: number;
  values: Record<string, unknown>;
  values_en?: Record<string, unknown> | null;
  field_labels: Record<string, string>;
  status: SubmissionStatus;
  created_at: string;
  taken_at: string | null;
  closed_at: string | null;
  assignee_admin_id: number | null;
  history?: StatusHistoryItem[];
  submitter?: Submitter | null;
  form_name?: string | null;
}

export interface ConversationItem {
  user_id: number;
  first_name: string | null;
  last_name: string | null;
  username: string | null;
  photo_url: string | null;
  system: System;
  last_message_text: string | null;
  last_message_at: string | null;
  unread_count: number;
  has_open_ticket: boolean;
}

export interface AttachmentRef {
  id?: number;
  url: string;
  name?: string | null;
  mime?: string | null;
  size?: number | null;
}

export interface MessageItem {
  id: number;
  user_id: number;
  system: System;
  direction: "in" | "out";
  text: string | null;
  attachments: AttachmentRef[] | null;
  is_ai_answered: boolean;
  ai_classification: string | null;
  replied_by_admin_id: number | null;
  replied_by_admin_name: string | null;
  created_at: string;
}

export interface UserSummary {
  id: number;
  user_id: string;
  system: System;
  first_name: string | null;
  last_name: string | null;
  patronymic: string | null;
  username: string | null;
  photo_url: string | null;
  phone: string | null;
  phone_verified: boolean;
  email: string | null;
  birth_date: string | null;
  study_group: string | null;
  ban_chat: boolean;
  ban_chat_reason: string | null;
  ban_forms: boolean;
  ban_forms_reason: string | null;
  ban_app: boolean;
  ban_app_reason: string | null;
  created_at: string;
}

export interface StatsOverview {
  days: number;
  bar: Array<{ form_id: number; name: string; count: number }>;
  timeseries: Array<{ day: string | null; count: number }>;
  kpi: {
    avg_new_to_work_seconds: number;
    avg_work_to_done_seconds: number;
    rejected_share: number;
    total: number;
    by_status: Record<string, number>;
    users_total: number;
    users_with_submission: number;
    conversion_rate: number;
  };
}

export interface TicketsOverview {
  open_count: number;
  unread_count: number;
}
