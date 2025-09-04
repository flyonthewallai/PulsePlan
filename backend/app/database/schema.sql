-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.annotation_tag_entity (
  id character varying NOT NULL,
  name character varying NOT NULL,
  createdAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  CONSTRAINT annotation_tag_entity_pkey PRIMARY KEY (id)
);
CREATE TABLE public.assignments (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  canvas_id bigint NOT NULL UNIQUE,
  course_id bigint,
  name text NOT NULL,
  due_at timestamp with time zone,
  type text DEFAULT 'assignment'::text,
  html_url text,
  submission_type text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT assignments_pkey PRIMARY KEY (id),
  CONSTRAINT assignments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.auth_identity (
  userId uuid,
  providerId character varying NOT NULL,
  providerType character varying NOT NULL,
  createdAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  CONSTRAINT auth_identity_pkey PRIMARY KEY (providerId, providerType),
  CONSTRAINT auth_identity_userId_fkey FOREIGN KEY (userId) REFERENCES public.user(id)
);
CREATE TABLE public.auth_provider_sync_history (
  id integer NOT NULL DEFAULT nextval('auth_provider_sync_history_id_seq'::regclass),
  providerType character varying NOT NULL,
  runMode text NOT NULL,
  status text NOT NULL,
  startedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
  endedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
  scanned integer NOT NULL,
  created integer NOT NULL,
  updated integer NOT NULL,
  disabled integer NOT NULL,
  error text,
  CONSTRAINT auth_provider_sync_history_pkey PRIMARY KEY (id)
);
CREATE TABLE public.calendar_events (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  provider text NOT NULL CHECK (provider = ANY (ARRAY['google'::text, 'microsoft'::text, 'apple'::text])),
  external_id text NOT NULL,
  calendar_id text NOT NULL,
  title text NOT NULL,
  description text,
  start_time timestamp with time zone NOT NULL,
  end_time timestamp with time zone NOT NULL,
  location text,
  status text,
  html_link text,
  attendees jsonb,
  creator_email text,
  organizer_email text,
  color_id text,
  transparency text,
  visibility text,
  is_all_day boolean DEFAULT false,
  is_cancelled boolean DEFAULT false,
  has_attachments boolean DEFAULT false,
  categories jsonb,
  importance text,
  sensitivity text,
  recurrence jsonb,
  created_at timestamp with time zone,
  updated_at timestamp with time zone,
  synced_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT calendar_events_pkey PRIMARY KEY (id),
  CONSTRAINT calendar_events_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
CREATE TABLE public.calendar_preferences (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL UNIQUE,
  auto_sync_enabled boolean DEFAULT true,
  sync_frequency_minutes integer DEFAULT 60,
  sync_period_days integer DEFAULT 30,
  include_all_calendars boolean DEFAULT false,
  selected_calendar_ids jsonb,
  conflict_resolution_strategy text DEFAULT 'manual'::text CHECK (conflict_resolution_strategy = ANY (ARRAY['manual'::text, 'prefer_google'::text, 'prefer_microsoft'::text, 'prefer_newest'::text])),
  create_external_events boolean DEFAULT true,
  sync_categories jsonb,
  notification_preferences jsonb,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT calendar_preferences_pkey PRIMARY KEY (id),
  CONSTRAINT calendar_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
CREATE TABLE public.calendar_sync_conflicts (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  event1_id uuid NOT NULL,
  event2_id uuid NOT NULL,
  conflict_type text NOT NULL CHECK (conflict_type = ANY (ARRAY['duplicate'::text, 'overlap'::text, 'similar'::text])),
  confidence_score numeric DEFAULT 0.0,
  resolution_status text DEFAULT 'unresolved'::text CHECK (resolution_status = ANY (ARRAY['unresolved'::text, 'resolved'::text, 'ignored'::text])),
  resolution_action text,
  detected_at timestamp with time zone NOT NULL DEFAULT now(),
  resolved_at timestamp with time zone,
  CONSTRAINT calendar_sync_conflicts_pkey PRIMARY KEY (id),
  CONSTRAINT calendar_sync_conflicts_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id),
  CONSTRAINT calendar_sync_conflicts_event2_id_fkey FOREIGN KEY (event2_id) REFERENCES public.calendar_events(id),
  CONSTRAINT calendar_sync_conflicts_event1_id_fkey FOREIGN KEY (event1_id) REFERENCES public.calendar_events(id)
);
CREATE TABLE public.calendar_sync_logs (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  sync_type text NOT NULL CHECK (sync_type = ANY (ARRAY['manual'::text, 'auto'::text, 'webhook'::text])),
  provider text NOT NULL,
  operation text NOT NULL CHECK (operation = ANY (ARRAY['sync'::text, 'create'::text, 'update'::text, 'delete'::text])),
  status text NOT NULL CHECK (status = ANY (ARRAY['success'::text, 'failure'::text, 'partial'::text])),
  events_processed integer DEFAULT 0,
  conflicts_detected integer DEFAULT 0,
  execution_time_ms integer,
  error_details jsonb,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT calendar_sync_logs_pkey PRIMARY KEY (id),
  CONSTRAINT calendar_sync_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
CREATE TABLE public.calendar_sync_status (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL UNIQUE,
  last_sync_at timestamp with time zone,
  sync_status text NOT NULL DEFAULT 'never_synced'::text CHECK (sync_status = ANY (ARRAY['success'::text, 'partial_failure'::text, 'failure'::text, 'never_synced'::text, 'in_progress'::text])),
  synced_events_count integer DEFAULT 0,
  errors jsonb,
  conflicts_count integer DEFAULT 0,
  google_events integer DEFAULT 0,
  microsoft_events integer DEFAULT 0,
  apple_events integer DEFAULT 0,
  sync_settings jsonb,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT calendar_sync_status_pkey PRIMARY KEY (id),
  CONSTRAINT calendar_sync_status_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
CREATE TABLE public.calendar_webhook_subscriptions (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  provider text NOT NULL CHECK (provider = ANY (ARRAY['google'::text, 'microsoft'::text])),
  subscription_id text NOT NULL,
  resource_uri text,
  expiration_time timestamp with time zone,
  is_active boolean DEFAULT true,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT calendar_webhook_subscriptions_pkey PRIMARY KEY (id),
  CONSTRAINT calendar_webhook_subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
CREATE TABLE public.canvas_integrations (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL UNIQUE,
  is_active boolean DEFAULT false,
  last_sync timestamp with time zone,
  assignments_synced integer DEFAULT 0,
  extension_version character varying,
  sync_source character varying,
  connection_code character varying,
  connection_code_expiry timestamp with time zone,
  connected_at timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT canvas_integrations_pkey PRIMARY KEY (id),
  CONSTRAINT canvas_integrations_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
CREATE TABLE public.credentials_entity (
  name character varying NOT NULL,
  data text NOT NULL,
  type character varying NOT NULL,
  createdAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  id character varying NOT NULL,
  isManaged boolean NOT NULL DEFAULT false,
  CONSTRAINT credentials_entity_pkey PRIMARY KEY (id)
);
CREATE TABLE public.daily_analytics (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  date date NOT NULL,
  total_planned_minutes integer DEFAULT 0,
  total_completed_minutes integer DEFAULT 0,
  tasks_planned integer DEFAULT 0,
  tasks_completed integer DEFAULT 0,
  subjects_data jsonb DEFAULT '{}'::jsonb,
  productivity_score numeric DEFAULT 0,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT daily_analytics_pkey PRIMARY KEY (id),
  CONSTRAINT daily_analytics_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.event_attendees (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  event_id uuid NOT NULL,
  user_id uuid NOT NULL,
  email character varying,
  name character varying,
  status character varying NOT NULL DEFAULT 'pending'::character varying CHECK (status::text = ANY (ARRAY['pending'::character varying::text, 'accepted'::character varying::text, 'declined'::character varying::text, 'tentative'::character varying::text])),
  is_organizer boolean NOT NULL DEFAULT false,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT event_attendees_pkey PRIMARY KEY (id),
  CONSTRAINT event_attendees_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id),
  CONSTRAINT event_attendees_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.event_destinations (
  id uuid NOT NULL,
  destination jsonb NOT NULL,
  createdAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  CONSTRAINT event_destinations_pkey PRIMARY KEY (id)
);
CREATE TABLE public.event_reminders (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  event_id uuid NOT NULL,
  user_id uuid NOT NULL,
  reminder_time timestamp with time zone NOT NULL,
  status character varying NOT NULL DEFAULT 'pending'::character varying CHECK (status::text = ANY (ARRAY['pending'::character varying::text, 'sent'::character varying::text, 'cancelled'::character varying::text])),
  type character varying NOT NULL DEFAULT 'notification'::character varying CHECK (type::text = ANY (ARRAY['notification'::character varying::text, 'email'::character varying::text, 'sms'::character varying::text])),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT event_reminders_pkey PRIMARY KEY (id),
  CONSTRAINT event_reminders_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id),
  CONSTRAINT event_reminders_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.events (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  title character varying NOT NULL,
  description text,
  type character varying NOT NULL CHECK (type::text = ANY (ARRAY['exam'::character varying::text, 'meeting'::character varying::text, 'appointment'::character varying::text, 'deadline'::character varying::text, 'class'::character varying::text, 'social'::character varying::text, 'personal'::character varying::text, 'work'::character varying::text, 'other'::character varying::text])),
  subject character varying,
  start_date timestamp with time zone NOT NULL,
  end_date timestamp with time zone,
  all_day boolean NOT NULL DEFAULT false,
  location character varying,
  location_type character varying CHECK (location_type::text = ANY (ARRAY['in_person'::character varying::text, 'virtual'::character varying::text, 'hybrid'::character varying::text])),
  meeting_url text,
  priority character varying NOT NULL DEFAULT 'medium'::character varying CHECK (priority::text = ANY (ARRAY['low'::character varying::text, 'medium'::character varying::text, 'high'::character varying::text, 'critical'::character varying::text])),
  reminder_minutes ARRAY,
  status character varying NOT NULL DEFAULT 'scheduled'::character varying CHECK (status::text = ANY (ARRAY['scheduled'::character varying::text, 'in_progress'::character varying::text, 'completed'::character varying::text, 'cancelled'::character varying::text, 'rescheduled'::character varying::text])),
  attendance_status character varying CHECK (attendance_status::text = ANY (ARRAY['attending'::character varying::text, 'maybe'::character varying::text, 'not_attending'::character varying::text, 'tentative'::character varying::text])),
  is_recurring boolean NOT NULL DEFAULT false,
  recurrence_pattern character varying CHECK (recurrence_pattern::text = ANY (ARRAY['daily'::character varying::text, 'weekly'::character varying::text, 'monthly'::character varying::text, 'yearly'::character varying::text])),
  recurrence_interval integer DEFAULT 1,
  recurrence_end_date timestamp with time zone,
  parent_event_id uuid,
  color character varying,
  tags ARRAY,
  attendees ARRAY,
  preparation_time_minutes integer DEFAULT 0 CHECK (preparation_time_minutes >= 0),
  external_calendar_id character varying,
  external_event_id character varying,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  canvas_assignment_id bigint UNIQUE,
  canvas_quiz_id bigint UNIQUE,
  sync_source text DEFAULT 'manual'::text CHECK (sync_source = ANY (ARRAY['manual'::text, 'google'::text, 'microsoft'::text, 'apple'::text])),
  last_synced_at timestamp with time zone,
  CONSTRAINT events_pkey PRIMARY KEY (id),
  CONSTRAINT events_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id),
  CONSTRAINT events_parent_event_id_fkey FOREIGN KEY (parent_event_id) REFERENCES public.events(id)
);
CREATE TABLE public.execution_annotation_tags (
  annotationId integer NOT NULL,
  tagId character varying NOT NULL,
  CONSTRAINT execution_annotation_tags_pkey PRIMARY KEY (annotationId, tagId),
  CONSTRAINT FK_a3697779b366e131b2bbdae2976 FOREIGN KEY (tagId) REFERENCES public.annotation_tag_entity(id),
  CONSTRAINT FK_c1519757391996eb06064f0e7c8 FOREIGN KEY (annotationId) REFERENCES public.execution_annotations(id)
);
CREATE TABLE public.execution_annotations (
  id integer NOT NULL DEFAULT nextval('execution_annotations_id_seq'::regclass),
  executionId integer NOT NULL,
  vote character varying,
  note text,
  createdAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  CONSTRAINT execution_annotations_pkey PRIMARY KEY (id),
  CONSTRAINT FK_97f863fa83c4786f19565084960 FOREIGN KEY (executionId) REFERENCES public.execution_entity(id)
);
CREATE TABLE public.execution_data (
  executionId integer NOT NULL,
  workflowData json NOT NULL,
  data text NOT NULL,
  CONSTRAINT execution_data_pkey PRIMARY KEY (executionId),
  CONSTRAINT execution_data_fk FOREIGN KEY (executionId) REFERENCES public.execution_entity(id)
);
CREATE TABLE public.execution_entity (
  id integer NOT NULL DEFAULT nextval('execution_entity_id_seq'::regclass),
  finished boolean NOT NULL,
  mode character varying NOT NULL,
  retryOf character varying,
  retrySuccessId character varying,
  startedAt timestamp with time zone,
  stoppedAt timestamp with time zone,
  waitTill timestamp with time zone,
  status character varying NOT NULL,
  workflowId character varying NOT NULL,
  deletedAt timestamp with time zone,
  createdAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  CONSTRAINT execution_entity_pkey PRIMARY KEY (id),
  CONSTRAINT fk_execution_entity_workflow_id FOREIGN KEY (workflowId) REFERENCES public.workflow_entity(id)
);
CREATE TABLE public.execution_metadata (
  id integer NOT NULL DEFAULT nextval('execution_metadata_temp_id_seq'::regclass),
  executionId integer NOT NULL,
  key character varying NOT NULL,
  value text NOT NULL,
  CONSTRAINT execution_metadata_pkey PRIMARY KEY (id),
  CONSTRAINT FK_31d0b4c93fb85ced26f6005cda3 FOREIGN KEY (executionId) REFERENCES public.execution_entity(id)
);
CREATE TABLE public.folder (
  id character varying NOT NULL,
  name character varying NOT NULL,
  parentFolderId character varying,
  projectId character varying NOT NULL,
  createdAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  CONSTRAINT folder_pkey PRIMARY KEY (id),
  CONSTRAINT FK_804ea52f6729e3940498bd54d78 FOREIGN KEY (parentFolderId) REFERENCES public.folder(id),
  CONSTRAINT FK_a8260b0b36939c6247f385b8221 FOREIGN KEY (projectId) REFERENCES public.project(id)
);
CREATE TABLE public.folder_tag (
  folderId character varying NOT NULL,
  tagId character varying NOT NULL,
  CONSTRAINT folder_tag_pkey PRIMARY KEY (folderId, tagId),
  CONSTRAINT FK_dc88164176283de80af47621746 FOREIGN KEY (tagId) REFERENCES public.tag_entity(id),
  CONSTRAINT FK_94a60854e06f2897b2e0d39edba FOREIGN KEY (folderId) REFERENCES public.folder(id)
);
CREATE TABLE public.goals (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  title text NOT NULL,
  description text,
  target_value numeric,
  current_value numeric DEFAULT 0,
  unit text,
  goal_type text,
  target_date date,
  status text DEFAULT 'active'::text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT goals_pkey PRIMARY KEY (id),
  CONSTRAINT goals_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.insights_by_period (
  id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  metaId integer NOT NULL,
  type integer NOT NULL,
  value integer NOT NULL,
  periodUnit integer NOT NULL,
  periodStart timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT insights_by_period_pkey PRIMARY KEY (id),
  CONSTRAINT FK_6414cfed98daabbfdd61a1cfbc0 FOREIGN KEY (metaId) REFERENCES public.insights_metadata(metaId)
);
CREATE TABLE public.insights_metadata (
  metaId integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  workflowId character varying,
  projectId character varying,
  workflowName character varying NOT NULL,
  projectName character varying NOT NULL,
  CONSTRAINT insights_metadata_pkey PRIMARY KEY (metaId),
  CONSTRAINT FK_1d8ab99d5861c9388d2dc1cf733 FOREIGN KEY (workflowId) REFERENCES public.workflow_entity(id),
  CONSTRAINT FK_2375a1eda085adb16b24615b69c FOREIGN KEY (projectId) REFERENCES public.project(id)
);
CREATE TABLE public.insights_raw (
  id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  metaId integer NOT NULL,
  type integer NOT NULL,
  value integer NOT NULL,
  timestamp timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT insights_raw_pkey PRIMARY KEY (id),
  CONSTRAINT FK_6e2e33741adef2a7c5d66befa4e FOREIGN KEY (metaId) REFERENCES public.insights_metadata(metaId)
);
CREATE TABLE public.installed_nodes (
  name character varying NOT NULL,
  type character varying NOT NULL,
  latestVersion integer NOT NULL DEFAULT 1,
  package character varying NOT NULL,
  CONSTRAINT installed_nodes_pkey PRIMARY KEY (name),
  CONSTRAINT FK_73f857fc5dce682cef8a99c11dbddbc969618951 FOREIGN KEY (package) REFERENCES public.installed_packages(packageName)
);
CREATE TABLE public.installed_packages (
  packageName character varying NOT NULL,
  installedVersion character varying NOT NULL,
  authorName character varying,
  authorEmail character varying,
  createdAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  CONSTRAINT installed_packages_pkey PRIMARY KEY (packageName)
);
CREATE TABLE public.invalid_auth_token (
  token character varying NOT NULL,
  expiresAt timestamp with time zone NOT NULL,
  CONSTRAINT invalid_auth_token_pkey PRIMARY KEY (token)
);
CREATE TABLE public.ios_devices (
  id integer NOT NULL DEFAULT nextval('ios_devices_id_seq'::regclass),
  user_id uuid NOT NULL,
  device_token character varying NOT NULL UNIQUE,
  device_model character varying,
  ios_version character varying,
  app_version character varying,
  is_active boolean NOT NULL DEFAULT true,
  registered_at timestamp with time zone NOT NULL DEFAULT now(),
  last_used_at timestamp with time zone,
  unregistered_at timestamp with time zone,
  failure_count integer NOT NULL DEFAULT 0,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT ios_devices_pkey PRIMARY KEY (id),
  CONSTRAINT ios_devices_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.migrations (
  id integer NOT NULL DEFAULT nextval('migrations_id_seq'::regclass),
  timestamp bigint NOT NULL,
  name character varying NOT NULL,
  CONSTRAINT migrations_pkey PRIMARY KEY (id)
);
CREATE TABLE public.notification_logs (
  id integer NOT NULL DEFAULT nextval('notification_logs_id_seq'::regclass),
  user_id uuid NOT NULL,
  notification_type character varying NOT NULL,
  title character varying NOT NULL,
  body text,
  category character varying,
  priority character varying NOT NULL DEFAULT 'normal'::character varying,
  success boolean NOT NULL,
  devices_targeted integer NOT NULL DEFAULT 1,
  devices_successful integer NOT NULL DEFAULT 0,
  apns_response_code integer,
  apns_response_body text,
  sent_at timestamp with time zone NOT NULL DEFAULT now(),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT notification_logs_pkey PRIMARY KEY (id),
  CONSTRAINT notification_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.notification_preferences (
  id integer NOT NULL DEFAULT nextval('notification_preferences_id_seq'::regclass),
  user_id uuid NOT NULL UNIQUE,
  daily_briefing_enabled boolean NOT NULL DEFAULT true,
  daily_briefing_time time without time zone NOT NULL DEFAULT '08:00:00'::time without time zone,
  weekly_summary_enabled boolean NOT NULL DEFAULT true,
  due_date_reminders_enabled boolean NOT NULL DEFAULT true,
  achievement_notifications_enabled boolean NOT NULL DEFAULT true,
  contextual_notifications_enabled boolean NOT NULL DEFAULT true,
  conflict_notifications_enabled boolean NOT NULL DEFAULT true,
  schedule_change_notifications_enabled boolean NOT NULL DEFAULT true,
  urgent_deadline_notifications_enabled boolean NOT NULL DEFAULT true,
  smart_suggestion_notifications_enabled boolean NOT NULL DEFAULT true,
  workload_warning_notifications_enabled boolean NOT NULL DEFAULT true,
  notification_sound character varying DEFAULT 'default'::character varying,
  notification_badge_enabled boolean NOT NULL DEFAULT true,
  quiet_hours_enabled boolean NOT NULL DEFAULT false,
  quiet_hours_start time without time zone DEFAULT '22:00:00'::time without time zone,
  quiet_hours_end time without time zone DEFAULT '08:00:00'::time without time zone,
  timezone character varying DEFAULT 'UTC'::character varying,
  max_notifications_per_hour integer NOT NULL DEFAULT 10,
  max_contextual_notifications_per_hour integer NOT NULL DEFAULT 5,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT notification_preferences_pkey PRIMARY KEY (id),
  CONSTRAINT notification_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.notification_rate_limits (
  id integer NOT NULL DEFAULT nextval('notification_rate_limits_id_seq'::regclass),
  user_id uuid NOT NULL,
  notification_type character varying NOT NULL,
  time_window timestamp with time zone NOT NULL,
  notification_count integer NOT NULL DEFAULT 1,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT notification_rate_limits_pkey PRIMARY KEY (id),
  CONSTRAINT notification_rate_limits_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.notification_templates (
  id integer NOT NULL DEFAULT nextval('notification_templates_id_seq'::regclass),
  template_key character varying NOT NULL UNIQUE,
  template_name character varying NOT NULL,
  title_template character varying NOT NULL,
  body_template text NOT NULL,
  category character varying,
  priority character varying NOT NULL DEFAULT 'normal'::character varying,
  template_variables jsonb,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT notification_templates_pkey PRIMARY KEY (id)
);
CREATE TABLE public.oauth_tokens (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  provider text NOT NULL CHECK (provider = ANY (ARRAY['google'::text, 'outlook'::text, 'apple'::text])),
  access_token text NOT NULL,
  refresh_token text NOT NULL,
  expires_at timestamp with time zone NOT NULL,
  scopes ARRAY,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  email text,
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT oauth_tokens_pkey PRIMARY KEY (id),
  CONSTRAINT calendar_connections_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.processed_data (
  workflowId character varying NOT NULL,
  context character varying NOT NULL,
  createdAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  value text NOT NULL,
  CONSTRAINT processed_data_pkey PRIMARY KEY (workflowId, context),
  CONSTRAINT FK_06a69a7032c97a763c2c7599464 FOREIGN KEY (workflowId) REFERENCES public.workflow_entity(id)
);
CREATE TABLE public.profiles (
  id uuid NOT NULL,
  full_name text,
  city text,
  timezone text,
  preferences jsonb DEFAULT '{"theme": "light", "language": "en", "notifications": true}'::jsonb,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT profiles_pkey PRIMARY KEY (id),
  CONSTRAINT profiles_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id)
);
CREATE TABLE public.project (
  id character varying NOT NULL,
  name character varying NOT NULL,
  type character varying NOT NULL,
  createdAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  icon json,
  CONSTRAINT project_pkey PRIMARY KEY (id)
);
CREATE TABLE public.project_relation (
  projectId character varying NOT NULL,
  userId uuid NOT NULL,
  role character varying NOT NULL,
  createdAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  CONSTRAINT project_relation_pkey PRIMARY KEY (projectId, userId),
  CONSTRAINT FK_5f0643f6717905a05164090dde7 FOREIGN KEY (userId) REFERENCES public.user(id),
  CONSTRAINT FK_61448d56d61802b5dfde5cdb002 FOREIGN KEY (projectId) REFERENCES public.project(id)
);
CREATE TABLE public.schedule_blocks (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  task_id uuid,
  start_time timestamp with time zone NOT NULL,
  end_time timestamp with time zone NOT NULL,
  status text NOT NULL DEFAULT 'scheduled'::text,
  notes text,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT schedule_blocks_pkey PRIMARY KEY (id),
  CONSTRAINT schedule_blocks_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id),
  CONSTRAINT schedule_blocks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.scheduled_notifications (
  id integer NOT NULL DEFAULT nextval('scheduled_notifications_id_seq'::regclass),
  user_id uuid NOT NULL,
  notification_type character varying NOT NULL,
  title character varying NOT NULL,
  body text NOT NULL,
  notification_data jsonb,
  scheduled_for timestamp with time zone NOT NULL,
  status character varying NOT NULL DEFAULT 'pending'::character varying CHECK (status::text = ANY (ARRAY['pending'::character varying, 'sent'::character varying, 'failed'::character varying, 'cancelled'::character varying]::text[])),
  attempts integer NOT NULL DEFAULT 0,
  max_attempts integer NOT NULL DEFAULT 3,
  last_attempt_at timestamp with time zone,
  sent_at timestamp with time zone,
  error_message text,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT scheduled_notifications_pkey PRIMARY KEY (id),
  CONSTRAINT scheduled_notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.scheduler_blocks (
  id text NOT NULL,
  user_id uuid NOT NULL,
  task_id text NOT NULL,
  start_time timestamp with time zone NOT NULL,
  end_time timestamp with time zone NOT NULL,
  estimated_completion_probability real DEFAULT 0.0,
  utility_score real DEFAULT 0.0,
  penalties_applied jsonb DEFAULT '{}'::jsonb,
  alternatives jsonb DEFAULT '[]'::jsonb,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT scheduler_blocks_pkey PRIMARY KEY (id),
  CONSTRAINT scheduler_blocks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id),
  CONSTRAINT scheduler_blocks_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.scheduler_tasks(id)
);
CREATE TABLE public.scheduler_busy_events (
  id text NOT NULL,
  user_id uuid NOT NULL,
  source text NOT NULL CHECK (source = ANY (ARRAY['google'::text, 'microsoft'::text, 'pulse'::text])),
  start_time timestamp with time zone NOT NULL,
  end_time timestamp with time zone NOT NULL,
  title text NOT NULL,
  movable boolean DEFAULT false,
  hard boolean DEFAULT true,
  location text,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT scheduler_busy_events_pkey PRIMARY KEY (id),
  CONSTRAINT scheduler_busy_events_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.scheduler_completion_events (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  task_id text NOT NULL,
  scheduled_slot timestamp with time zone NOT NULL,
  completed_at timestamp with time zone,
  skipped boolean DEFAULT false,
  delay_minutes integer DEFAULT 0,
  rescheduled_count integer DEFAULT 0,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT scheduler_completion_events_pkey PRIMARY KEY (id),
  CONSTRAINT scheduler_completion_events_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.scheduler_models (
  id text NOT NULL,
  user_id uuid NOT NULL,
  model_type text NOT NULL CHECK (model_type = ANY (ARRAY['completion_model'::text, 'bandit_weights'::text])),
  model_data jsonb NOT NULL,
  version integer DEFAULT 1,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT scheduler_models_pkey PRIMARY KEY (id),
  CONSTRAINT scheduler_models_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.scheduler_preferences (
  user_id uuid NOT NULL,
  timezone text NOT NULL DEFAULT 'UTC'::text,
  workday_start text DEFAULT '08:30'::text,
  workday_end text DEFAULT '22:00'::text,
  break_every_minutes integer DEFAULT 50,
  break_duration_minutes integer DEFAULT 10,
  deep_work_windows jsonb DEFAULT '[]'::jsonb,
  no_study_windows jsonb DEFAULT '[]'::jsonb,
  max_daily_effort_minutes integer DEFAULT 480,
  max_concurrent_courses integer DEFAULT 3,
  spacing_policy jsonb DEFAULT '{}'::jsonb,
  latenight_penalty real DEFAULT 3.0,
  morning_penalty real DEFAULT 1.0,
  context_switch_penalty real DEFAULT 2.0,
  min_gap_between_blocks integer DEFAULT 15,
  session_granularity_minutes integer DEFAULT 30 CHECK (session_granularity_minutes = ANY (ARRAY[15, 30])),
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT scheduler_preferences_pkey PRIMARY KEY (user_id),
  CONSTRAINT scheduler_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.scheduler_runs (
  id text NOT NULL,
  user_id uuid NOT NULL,
  horizon_days integer NOT NULL,
  started_at timestamp with time zone NOT NULL,
  finished_at timestamp with time zone,
  status text NOT NULL DEFAULT 'pending'::text CHECK (status = ANY (ARRAY['pending'::text, 'running'::text, 'completed'::text, 'failed'::text, 'timeout'::text])),
  feasible boolean DEFAULT false,
  objective_value real DEFAULT 0.0,
  config jsonb DEFAULT '{}'::jsonb,
  weights jsonb DEFAULT '{}'::jsonb,
  diagnostics jsonb DEFAULT '{}'::jsonb,
  error_message text,
  CONSTRAINT scheduler_runs_pkey PRIMARY KEY (id),
  CONSTRAINT scheduler_runs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.scheduler_tasks (
  id text NOT NULL,
  user_id uuid NOT NULL,
  title text NOT NULL,
  kind text NOT NULL CHECK (kind = ANY (ARRAY['study'::text, 'assignment'::text, 'exam'::text, 'reading'::text, 'project'::text, 'hobby'::text, 'admin'::text])),
  estimated_minutes integer NOT NULL CHECK (estimated_minutes > 0),
  min_block_minutes integer NOT NULL CHECK (min_block_minutes > 0),
  max_block_minutes integer NOT NULL,
  deadline timestamp with time zone,
  earliest_start timestamp with time zone,
  preferred_windows jsonb DEFAULT '[]'::jsonb,
  avoid_windows jsonb DEFAULT '[]'::jsonb,
  fixed boolean DEFAULT false,
  parent_task_id text,
  prerequisites ARRAY DEFAULT '{}'::text[],
  weight real DEFAULT 1.0 CHECK (weight >= 0::double precision),
  course_id text,
  must_finish_before text,
  tags ARRAY DEFAULT '{}'::text[],
  pinned_slots jsonb DEFAULT '[]'::jsonb,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT scheduler_tasks_pkey PRIMARY KEY (id),
  CONSTRAINT scheduler_tasks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id),
  CONSTRAINT scheduler_tasks_must_finish_before_fkey FOREIGN KEY (must_finish_before) REFERENCES public.scheduler_tasks(id),
  CONSTRAINT scheduler_tasks_parent_task_id_fkey FOREIGN KEY (parent_task_id) REFERENCES public.scheduler_tasks(id)
);
CREATE TABLE public.settings (
  key character varying NOT NULL,
  value text NOT NULL,
  loadOnStartup boolean NOT NULL DEFAULT false,
  CONSTRAINT settings_pkey PRIMARY KEY (key)
);
CREATE TABLE public.shared_credentials (
  credentialsId character varying NOT NULL,
  projectId character varying NOT NULL,
  role text NOT NULL,
  createdAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  CONSTRAINT shared_credentials_pkey PRIMARY KEY (credentialsId, projectId),
  CONSTRAINT FK_416f66fc846c7c442970c094ccf FOREIGN KEY (credentialsId) REFERENCES public.credentials_entity(id),
  CONSTRAINT FK_812c2852270da1247756e77f5a4 FOREIGN KEY (projectId) REFERENCES public.project(id)
);
CREATE TABLE public.shared_workflow (
  workflowId character varying NOT NULL,
  projectId character varying NOT NULL,
  role text NOT NULL,
  createdAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  CONSTRAINT shared_workflow_pkey PRIMARY KEY (workflowId, projectId),
  CONSTRAINT FK_daa206a04983d47d0a9c34649ce FOREIGN KEY (workflowId) REFERENCES public.workflow_entity(id),
  CONSTRAINT FK_a45ea5f27bcfdc21af9b4188560 FOREIGN KEY (projectId) REFERENCES public.project(id)
);
CREATE TABLE public.streaks (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  streak_type text NOT NULL,
  current_streak integer DEFAULT 0,
  longest_streak integer DEFAULT 0,
  last_activity_date date,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT streaks_pkey PRIMARY KEY (id),
  CONSTRAINT streaks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.subjects (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  name text NOT NULL,
  color text NOT NULL,
  icon text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT subjects_pkey PRIMARY KEY (id),
  CONSTRAINT subjects_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.subscriptions (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL,
  status text NOT NULL CHECK (status = ANY (ARRAY['active'::text, 'canceled'::text, 'incomplete'::text, 'incomplete_expired'::text, 'past_due'::text, 'trialing'::text, 'unpaid'::text])),
  stripe_customer_id text,
  stripe_subscription_id text,
  created_at timestamp with time zone NOT NULL DEFAULT timezone('utc'::text, now()),
  updated_at timestamp with time zone NOT NULL DEFAULT timezone('utc'::text, now()),
  CONSTRAINT subscriptions_pkey PRIMARY KEY (id),
  CONSTRAINT subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
CREATE TABLE public.tag_entity (
  name character varying NOT NULL,
  createdAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  id character varying NOT NULL,
  CONSTRAINT tag_entity_pkey PRIMARY KEY (id)
);
CREATE TABLE public.tasks (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  title text NOT NULL,
  due_date timestamp with time zone,
  estimated_minutes integer,
  subject text,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  description text,
  priority text,
  status text DEFAULT 'pending'::text,
  actual_minutes integer,
  completed_at timestamp with time zone,
  tags ARRAY,
  difficulty text CHECK (difficulty = ANY (ARRAY['easy'::text, 'medium'::text, 'hard'::text])),
  notes text,
  updated_at timestamp with time zone DEFAULT now(),
  source character varying DEFAULT 'manual'::character varying,
  canvas_id character varying,
  canvas_url text,
  canvas_grade jsonb,
  canvas_points numeric,
  canvas_max_points numeric,
  CONSTRAINT tasks_pkey PRIMARY KEY (id),
  CONSTRAINT tasks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.test_case_execution (
  id character varying NOT NULL,
  testRunId character varying NOT NULL,
  executionId integer,
  status character varying NOT NULL,
  runAt timestamp with time zone,
  completedAt timestamp with time zone,
  errorCode character varying,
  errorDetails json,
  metrics json,
  createdAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  CONSTRAINT test_case_execution_pkey PRIMARY KEY (id),
  CONSTRAINT FK_8e4b4774db42f1e6dda3452b2af FOREIGN KEY (testRunId) REFERENCES public.test_run(id),
  CONSTRAINT FK_e48965fac35d0f5b9e7f51d8c44 FOREIGN KEY (executionId) REFERENCES public.execution_entity(id)
);
CREATE TABLE public.test_run (
  id character varying NOT NULL,
  workflowId character varying NOT NULL,
  status character varying NOT NULL,
  errorCode character varying,
  errorDetails json,
  runAt timestamp with time zone,
  completedAt timestamp with time zone,
  metrics json,
  createdAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  CONSTRAINT test_run_pkey PRIMARY KEY (id),
  CONSTRAINT FK_d6870d3b6e4c185d33926f423c8 FOREIGN KEY (workflowId) REFERENCES public.workflow_entity(id)
);
CREATE TABLE public.time_sessions (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  task_id uuid,
  start_time timestamp with time zone NOT NULL,
  end_time timestamp with time zone,
  duration_minutes integer,
  session_type text DEFAULT 'work'::text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT time_sessions_pkey PRIMARY KEY (id),
  CONSTRAINT time_sessions_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id),
  CONSTRAINT time_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.todos (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL,
  title text NOT NULL CHECK (length(title) > 0 AND length(title) <= 500),
  description text CHECK (length(description) <= 2000),
  completed boolean NOT NULL DEFAULT false,
  priority USER-DEFINED NOT NULL DEFAULT 'medium'::todo_priority,
  status USER-DEFINED NOT NULL DEFAULT 'pending'::todo_status,
  due_date timestamp with time zone,
  tags ARRAY DEFAULT '{}'::text[],
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  completed_at timestamp with time zone,
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT todos_pkey PRIMARY KEY (id),
  CONSTRAINT todos_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
CREATE TABLE public.user (
  id uuid NOT NULL DEFAULT uuid_in((OVERLAY(OVERLAY(md5((((random())::text || ':'::text) || (clock_timestamp())::text)) PLACING '4'::text FROM 13) PLACING to_hex((floor(((random() * (((11 - 8) + 1))::double precision) + (8)::double precision)))::integer) FROM 17))::cstring),
  email character varying UNIQUE,
  firstName character varying,
  lastName character varying,
  password character varying,
  personalizationAnswers json,
  createdAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  settings json,
  disabled boolean NOT NULL DEFAULT false,
  mfaEnabled boolean NOT NULL DEFAULT false,
  mfaSecret text,
  mfaRecoveryCodes text,
  role text NOT NULL,
  CONSTRAINT user_pkey PRIMARY KEY (id)
);
CREATE TABLE public.user_api_keys (
  id character varying NOT NULL,
  userId uuid NOT NULL,
  label character varying NOT NULL,
  apiKey character varying NOT NULL,
  createdAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  scopes json,
  CONSTRAINT user_api_keys_pkey PRIMARY KEY (id),
  CONSTRAINT FK_e131705cbbc8fb589889b02d457 FOREIGN KEY (userId) REFERENCES public.user(id)
);
CREATE TABLE public.user_preferences (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  category text NOT NULL,
  preference_key text NOT NULL,
  value jsonb NOT NULL,
  description text,
  is_active boolean DEFAULT true,
  priority integer DEFAULT 1,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  daily_briefing_enabled boolean DEFAULT true,
  daily_briefing_time time without time zone DEFAULT '08:00:00'::time without time zone,
  daily_briefing_timezone character varying DEFAULT 'UTC'::character varying,
  daily_briefing_email_enabled boolean DEFAULT true,
  daily_briefing_notification_enabled boolean DEFAULT true,
  weekly_pulse_enabled boolean DEFAULT true,
  weekly_pulse_day integer DEFAULT 0,
  weekly_pulse_time time without time zone DEFAULT '18:00:00'::time without time zone,
  weekly_pulse_email_enabled boolean DEFAULT true,
  weekly_pulse_notification_enabled boolean DEFAULT true,
  briefing_content_preferences jsonb DEFAULT '{}'::jsonb,
  CONSTRAINT user_preferences_pkey PRIMARY KEY (id),
  CONSTRAINT user_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
CREATE TABLE public.users (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  email text NOT NULL UNIQUE,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  onboarding_complete boolean DEFAULT false,
  subscription_status text NOT NULL DEFAULT 'free'::text,
  apple_transaction_id text,
  subscription_expires_at timestamp with time zone,
  subscription_updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
  name text,
  avatar_url text,
  timezone text DEFAULT 'UTC'::text,
  last_login_at timestamp with time zone,
  preferences jsonb DEFAULT '{}'::jsonb,
  working_hours jsonb DEFAULT '{"endHour": 17, "startHour": 9}'::jsonb,
  onboarding_step integer DEFAULT 0,
  school text,
  memories jsonb DEFAULT '{}'::jsonb,
  academic_year text,
  user_type character varying CHECK (user_type::text = ANY (ARRAY['student'::character varying::text, 'professional'::character varying::text, 'educator'::character varying::text])),
  study_preferences jsonb,
  work_preferences jsonb,
  integration_preferences jsonb,
  notification_preferences jsonb,
  onboarding_completed_at timestamp with time zone,
  city text,
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT users_pkey PRIMARY KEY (id)
);
CREATE TABLE public.variables (
  key character varying NOT NULL UNIQUE,
  type character varying NOT NULL DEFAULT 'string'::character varying,
  value character varying,
  id character varying NOT NULL,
  CONSTRAINT variables_pkey PRIMARY KEY (id)
);
CREATE TABLE public.vec_memory (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  namespace text NOT NULL,
  doc_id text NOT NULL,
  chunk_id integer DEFAULT 0,
  content text,
  summary text,
  embedding USER-DEFINED NOT NULL,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT vec_memory_pkey PRIMARY KEY (id),
  CONSTRAINT vec_memory_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
CREATE TABLE public.webhook_entity (
  webhookPath character varying NOT NULL,
  method character varying NOT NULL,
  node character varying NOT NULL,
  webhookId character varying,
  pathLength integer,
  workflowId character varying NOT NULL,
  CONSTRAINT webhook_entity_pkey PRIMARY KEY (webhookPath, method),
  CONSTRAINT fk_webhook_entity_workflow_id FOREIGN KEY (workflowId) REFERENCES public.workflow_entity(id)
);
CREATE TABLE public.workflow_entity (
  name character varying NOT NULL,
  active boolean NOT NULL,
  nodes json NOT NULL,
  connections json NOT NULL,
  createdAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  settings json,
  staticData json,
  pinData json,
  versionId character,
  triggerCount integer NOT NULL DEFAULT 0,
  id character varying NOT NULL,
  meta json,
  parentFolderId character varying DEFAULT NULL::character varying,
  isArchived boolean NOT NULL DEFAULT false,
  CONSTRAINT workflow_entity_pkey PRIMARY KEY (id),
  CONSTRAINT fk_workflow_parent_folder FOREIGN KEY (parentFolderId) REFERENCES public.folder(id)
);
CREATE TABLE public.workflow_history (
  versionId character varying NOT NULL,
  workflowId character varying NOT NULL,
  authors character varying NOT NULL,
  createdAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  nodes json NOT NULL,
  connections json NOT NULL,
  CONSTRAINT workflow_history_pkey PRIMARY KEY (versionId),
  CONSTRAINT FK_1e31657f5fe46816c34be7c1b4b FOREIGN KEY (workflowId) REFERENCES public.workflow_entity(id)
);
CREATE TABLE public.workflow_statistics (
  count integer DEFAULT 0,
  latestEvent timestamp with time zone,
  name character varying NOT NULL,
  workflowId character varying NOT NULL,
  rootCount integer DEFAULT 0,
  CONSTRAINT workflow_statistics_pkey PRIMARY KEY (name, workflowId),
  CONSTRAINT fk_workflow_statistics_workflow_id FOREIGN KEY (workflowId) REFERENCES public.workflow_entity(id)
);
CREATE TABLE public.workflows_tags (
  workflowId character varying NOT NULL,
  tagId character varying NOT NULL,
  CONSTRAINT workflows_tags_pkey PRIMARY KEY (workflowId, tagId),
  CONSTRAINT fk_workflows_tags_workflow_id FOREIGN KEY (workflowId) REFERENCES public.workflow_entity(id),
  CONSTRAINT fk_workflows_tags_tag_id FOREIGN KEY (tagId) REFERENCES public.tag_entity(id)
);