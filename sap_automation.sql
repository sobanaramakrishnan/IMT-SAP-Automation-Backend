CREATE DATABASE IMT;

CREATE SCHEMA automation;

CREATE SEQUENCE automation.dc_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE automation.user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS automation.dc_details
(
    dc_id integer DEFAULT nextval('automation.dc_id_seq'::regclass),
    user_id integer,
    dc_number character varying(500) COLLATE pg_catalog."default" NOT NULL,
    part_name text COLLATE pg_catalog."default",
    part_number character varying(500) COLLATE pg_catalog."default",
    quantity integer,
    weight integer,
    image_path text COLLATE pg_catalog."default",
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    verified_by integer,
    verified_at timestamp without time zone,
    verified_status character varying(20) COLLATE pg_catalog."default",
    reviewed_weight numeric(10, 2),
    reviewed_quantity integer,
    process_type character varying(50) COLLATE pg_catalog."default",
    notification_sent boolean
);

CREATE TABLE IF NOT EXISTS automation.users
(
    user_id integer DEFAULT nextval('automation.user_id_seq'::regclass),
    username character varying(50) COLLATE pg_catalog."default",
    email character varying(100) COLLATE pg_catalog."default",
    password text COLLATE pg_catalog."default" NOT NULL,
    user_role character varying(30) COLLATE pg_catalog."default",
    marked_for_deletion character varying(1) COLLATE pg_catalog."default",
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT users_email_key UNIQUE (email)
);
