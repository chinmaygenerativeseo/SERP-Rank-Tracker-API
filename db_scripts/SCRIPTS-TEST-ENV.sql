
-- BELOW TABLE WILL STORE THE API CONFIGURATION
CREATE TABLE api_config (
	api_config_id BIGINT IDENTITY(1,1) PRIMARY KEY,
	api_provider VARCHAR(100) NOT NULL,
	api_provider_username varchar(200),
	api_provider_password varchar(200),
	base_url NVARCHAR(1000) NOT NULL,
	auth_type VARCHAR(50) NOT NULL, -- API_KEY / BEARER / BASIC / OAUTH2
	auth_key varchar(1000),
	api_description varchar(1000),
	status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
	created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE()
);



INSERT INTO api_config 
VALUES 
('hasdata','vernekargroup2026@gmail.com',NULL,'https://api.hasdata.com/','API_KEY','2dea73c2-6a8f-4b74-a45d-404d0f24a558',
'The Google SERP API provides real-time access to structured Google search results, offering no blocks or CAPTCHAs.',
'ACTIVE',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)


SELECT * FROM api_config


create table serp_rank_tracker (
	serp_rank_tracker_id BIGINT IDENTITY(1,1) PRIMARY KEY,
	domain varchar(1000) not null,
	keyword varchar(1000) not null,
	current_position BIGINT not null,
	previous_position BIGINT not null,
	created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE()
);

select * from serp_rank_tracker










