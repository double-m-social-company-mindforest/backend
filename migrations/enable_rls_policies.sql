-- Enable RLS for all public tables and create appropriate policies
-- Generated: 2025-09-01

-- ============================================
-- 1. Enable RLS on all tables
-- ============================================

-- Core tables
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.main_keywords ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sub_keywords ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.keyword_type_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.intermediate_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.final_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.type_combinations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.calculation_weights ENABLE ROW LEVEL SECURITY;

-- Consultation tables
ALTER TABLE public.consultations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.consultation_cards ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.consultation_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.consultation_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.counseling_fields ENABLE ROW LEVEL SECURITY;

-- User tables
ALTER TABLE public.counselors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.admins ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.refresh_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.admin_refresh_tokens ENABLE ROW LEVEL SECURITY;

-- System tables
ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY;

-- ============================================
-- 2. Create RLS policies for read-only tables
-- ============================================

-- Categories (read-only for all)
CREATE POLICY "categories_read_all" ON public.categories
    FOR SELECT
    USING (true);

-- Main keywords (read-only for all)
CREATE POLICY "main_keywords_read_all" ON public.main_keywords
    FOR SELECT
    USING (true);

-- Sub keywords (read-only for all)
CREATE POLICY "sub_keywords_read_all" ON public.sub_keywords
    FOR SELECT
    USING (true);

-- Keyword type scores (read-only for all)
CREATE POLICY "keyword_type_scores_read_all" ON public.keyword_type_scores
    FOR SELECT
    USING (true);

-- Intermediate types (read-only for all)
CREATE POLICY "intermediate_types_read_all" ON public.intermediate_types
    FOR SELECT
    USING (true);

-- Final types (read-only for all)
CREATE POLICY "final_types_read_all" ON public.final_types
    FOR SELECT
    USING (true);

-- Type combinations (read-only for all)
CREATE POLICY "type_combinations_read_all" ON public.type_combinations
    FOR SELECT
    USING (true);

-- Calculation weights (read-only for all)
CREATE POLICY "calculation_weights_read_all" ON public.calculation_weights
    FOR SELECT
    USING (true);

-- Counseling fields (read-only for all)
CREATE POLICY "counseling_fields_read_all" ON public.counseling_fields
    FOR SELECT
    USING (true);

-- ============================================
-- 3. Create RLS policies for consultation tables
-- ============================================

-- Consultations (service account full access)
CREATE POLICY "consultations_service_full_access" ON public.consultations
    FOR ALL
    USING (auth.role() = 'service_role');

-- Consultation cards (service account full access)
CREATE POLICY "consultation_cards_service_full_access" ON public.consultation_cards
    FOR ALL
    USING (auth.role() = 'service_role');

-- Consultation messages (service account full access)
CREATE POLICY "consultation_messages_service_full_access" ON public.consultation_messages
    FOR ALL
    USING (auth.role() = 'service_role');

-- Consultation requests (service account full access)
CREATE POLICY "consultation_requests_service_full_access" ON public.consultation_requests
    FOR ALL
    USING (auth.role() = 'service_role');

-- ============================================
-- 4. Create RLS policies for user tables
-- ============================================

-- Counselors (service account full access)
CREATE POLICY "counselors_service_full_access" ON public.counselors
    FOR ALL
    USING (auth.role() = 'service_role');

-- Admins (service account full access)
CREATE POLICY "admins_service_full_access" ON public.admins
    FOR ALL
    USING (auth.role() = 'service_role');

-- Refresh tokens (service account full access)
CREATE POLICY "refresh_tokens_service_full_access" ON public.refresh_tokens
    FOR ALL
    USING (auth.role() = 'service_role');

-- Admin refresh tokens (service account full access)
CREATE POLICY "admin_refresh_tokens_service_full_access" ON public.admin_refresh_tokens
    FOR ALL
    USING (auth.role() = 'service_role');

-- ============================================
-- 5. Create RLS policies for system tables
-- ============================================

-- Alembic version (service account full access)
CREATE POLICY "alembic_version_service_full_access" ON public.alembic_version
    FOR ALL
    USING (auth.role() = 'service_role');

-- ============================================
-- 6. Fix function search path issues
-- ============================================

-- Update the update_updated_at_column function
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Update the delete_expired_refresh_tokens function
CREATE OR REPLACE FUNCTION public.delete_expired_refresh_tokens()
RETURNS void
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    DELETE FROM public.refresh_tokens
    WHERE expires_at < NOW();
    
    DELETE FROM public.admin_refresh_tokens
    WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;