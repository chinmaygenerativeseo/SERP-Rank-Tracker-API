-- SQL Server database schema initialization script
-- Run this script in your SQL Server database before starting the API server

-- 1. Create api_config Table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[api_config]') AND type in (N'U'))
BEGIN
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
    
    PRINT 'SUCCESS: Table [dbo].[api_config] created successfully.';
END
ELSE
BEGIN
    PRINT 'INFO: Table [dbo].[api_config] already exists.';
END
GO

-- 2. Seed Sample/Diagnostic Data (Optional)
-- Insert standard initial tracking configurations for testing purposes
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[api_config]') AND type in (N'U'))
BEGIN
    IF NOT EXISTS (SELECT 1 FROM [dbo].[api_config] WHERE [api_provider] = 'Google Search Console')
    BEGIN
        INSERT INTO [dbo].[api_config] (
            [api_provider], 
            [api_provider_username], 
            [api_provider_password], 
            [base_url], 
            [auth_type], 
            [auth_key], 
            [api_description], 
            [status]
        ) VALUES (
            'Google Search Console',
            'seo-analytics@company.com',
            NULL,
            'https://www.googleapis.com/webmasters/v3',
            'OAUTH2',
            'sample-oauth-refresh-token-xyz123',
            'Google Search Console API for keyword performance and search query analysis.',
            'ACTIVE'
        );
    END

    IF NOT EXISTS (SELECT 1 FROM [dbo].[api_config] WHERE [api_provider] = 'SEMrush')
    BEGIN
        INSERT INTO [dbo].[api_config] (
            [api_provider], 
            [api_provider_username], 
            [base_url], 
            [auth_type], 
            [auth_key], 
            [api_description], 
            [status]
        ) VALUES (
            'SEMrush',
            'seo-team@company.com',
            'https://api.semrush.com',
            'API_KEY',
            'semrush-premium-api-key-key-key',
            'SEMrush API config for keyword rank tracking and domain analysis.',
            'ACTIVE'
        );
    END

    IF NOT EXISTS (SELECT 1 FROM [dbo].[api_config] WHERE [api_provider] = 'HasData')
    BEGIN
        INSERT INTO [dbo].[api_config] (
            [api_provider], 
            [api_provider_username], 
            [base_url], 
            [auth_type], 
            [auth_key], 
            [api_description], 
            [status]
        ) VALUES (
            'HasData',
            'api-admin@company.com',
            'api.hasdata.com',
            'API_KEY',
            '2dea73c2-6a8f-4b74-a45d-404d0f24a558',
            'HasData Google Search Engine Results Page (SERP) Scraper and Rank Tracker API.',
            'ACTIVE'
        );
    END
    
    PRINT 'SUCCESS: Diagnostic seed data inserted.';
END
GO

-- 3. Create serp_rank_tracker Table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[serp_rank_tracker]') AND type in (N'U'))
BEGIN
    CREATE TABLE serp_rank_tracker (
        serp_rank_tracker_id BIGINT IDENTITY(1,1) PRIMARY KEY,
        domain varchar(1000) not null,
        keyword varchar(1000) not null,
        current_position BIGINT not null,
        previous_position BIGINT not null,
        created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
        updated_at DATETIME2 NOT NULL DEFAULT GETDATE()
    );
    
    PRINT 'SUCCESS: Table [dbo].[serp_rank_tracker] created successfully.';
END
ELSE
BEGIN
    PRINT 'INFO: Table [dbo].[serp_rank_tracker] already exists.';
END
GO

