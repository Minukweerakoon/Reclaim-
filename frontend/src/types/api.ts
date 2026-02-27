// ============================================================================
// VALIDATION TYPES  (matched to actual FastAPI backend response shapes)
// ============================================================================

export interface ValidationResponse {
    request_id: string;
    timestamp: string;
    input_types: string[];
    text?: TextValidationResult;
    image?: ImageValidationResult;
    voice?: VoiceValidationResult;
    confidence: ConfidenceScore;
    cross_modal?: CrossModal;
    feedback?: ValidationFeedback;
    clarification_questions?: string[];
    xai_heatmap_url?: string;
    /** Set when the item was successfully saved to Supabase (lost_items or found_items) */
    supabase_id?: string;
}

/* ---------- Text ---------- */

export interface TextValidationResult {
    text: string;
    timestamp: string;
    completeness: {
        valid: boolean;
        score: number;               // 0-100
        entities: Record<string, string[]>;
        missing_info: string[];
        has_brand: boolean;
        has_time: boolean;
        is_vague: boolean;
        vagueness_reasons: string[];
        feedback: string;
    };
    coherence: {
        valid: boolean;
        score: number;
        feedback: string;
    };
    entities: {
        entities: { text: string; label: string; start: number; end: number }[];
        item_mentions: string[];
        color_mentions: string[];
        location_mentions: string[];
        brand_mentions: string[];
        style_mentions: string[];
    };
    overall_score: number;            // 0-1
    valid: boolean;
    clarification_questions: string[];
}

/* ---------- Image ---------- */

export interface ImageValidationResult {
    image_path: string;
    timestamp: string;
    sharpness: {
        valid: boolean;
        score: number;
        raw_variance: number;
        feedback: string;
    };
    objects: {
        valid: boolean;
        confidence: number;
        detections: DetectedObject[];
        detection_score: number;
        feedback: string;
        model: string;
    };
    privacy: {
        faces_detected: number;
        privacy_protected: boolean;
        processed_image: string;
        feedback: string;
    };
    overall_score: number;            // 0-100
    valid: boolean;
}

export interface DetectedObject {
    class: string;
    original_class?: string;
    confidence: number;
    bbox: number[];
}

/* ---------- Voice ---------- */

export interface VoiceValidationResult {
    transcription: string;
    confidence: number;
    snr?: number;
    language: string;
    timestamp: string;
}

/* ---------- Confidence ---------- */

export interface ConfidenceScore {
    overall_confidence: number;
    raw_confidence: number;
    calibration_applied: boolean;
    routing: string;
    action: string;
    individual_scores: {
        image: number;
        text: number;
        voice: number;
    };
    cross_modal_scores?: {
        clip_similarity?: number;
        voice_text_similarity?: number;
    };
    active_weights: {
        image: number;
        text: number;
        voice: number;
        clip: number;
        voice_text: number;
    };
}

/* ---------- Cross-Modal ---------- */

export interface CrossModal {
    image_text?: {
        valid: boolean;
        similarity: number;
        threshold: number;
        feedback: string;
        mismatch_detection?: {
            mismatches: any[];
            attribute_scores?: {
                predicted_items?: [string, number][];
                predicted_colors?: [string, number][];
                mentioned_items?: string[];
                mentioned_colors?: string[];
            };
        };
        suggestions?: string[];
    };
    spatial_temporal?: {
        plausibility_score: number;
        valid: boolean;
        location_probability: number;
        time_probability: number;
        explanation: string;
        suggestions: string[];
        normalized_inputs?: Record<string, string>;
        confidence_level: string;
    };
}

/* ---------- Feedback ---------- */

export interface ValidationFeedback {
    suggestions: string[];
    missing_elements: string[];
    message: string;
}

/* ---------- UI-only helpers (not from backend) ---------- */

export interface Discrepancy {
    type: string;
    severity?: 'low' | 'medium' | 'high';
    description: string;
    message?: string;
}

export interface MissionReport {
    summary: string;
    recommendation: string;
}

// ============================================================================
// CHAT TYPES
// ============================================================================

export interface ChatMessage {
    role: 'user' | 'bot';
    content: string;
    timestamp?: string | Date;
}

export interface ChatRequest {
    message: string;
    history?: ChatMessage[];
    previous_prediction?: ValidationResponse;
    extracted_info?: Record<string, any>;
}

export interface ChatResponse {
    bot_response: string;
    intention: 'lost' | 'found' | 'unknown';
    extracted_info: Record<string, any>;
    next_action: string;
    sentiment: string;
    feedback_recorded?: boolean;
}

// ============================================================================
// REPORTS TYPES
// ============================================================================

export interface Report {
    id?: string;
    request_id: string;
    timestamp: string;
    user_id?: string;
    input_types?: string[];
    confidence?: ConfidenceScore;
    cross_modal?: CrossModal;
    status?: string;
    [key: string]: any;
}

export interface ReportsListResponse {
    reports: Report[];
    count: number;
}

// ============================================================================
// HEALTH TYPES
// ============================================================================

export interface HealthStatus {
    status: 'healthy' | 'degraded' | 'unhealthy';
    timestamp?: string;
    components?: {
        api: 'up' | 'down';
        redis: 'up' | 'down';
        validators: {
            image: 'up' | 'down';
            text: 'up' | 'down';
            voice: 'up' | 'down';
            clip: 'up' | 'down';
            consistency_engine?: 'up' | 'down';
        };
    };
    // Fallback fields for backwards compatibility
    redis?: 'up' | 'down';
    validators?: {
        text?: boolean;
        image?: boolean;
        voice?: boolean;
        clip?: boolean;
    };
    uptime?: number;
    total_processed?: number;
    total_discrepancies?: number;
    avg_latency?: string;
    accuracy?: string;
}

// ============================================================================
// WEBSOCKET TYPES
// ============================================================================

export interface WSProgressMessage {
    type: 'progress' | 'complete' | 'error' | 'ping' | 'pong' | 'connected';
    stage?: string;
    progress?: number;
    message?: string;
    result?: ValidationResponse;
    error?: string;
    client_id?: string;
    status?: string;
}

// ============================================================================
// FEEDBACK TYPES (Active Learning)
// ============================================================================

export interface FeedbackRequest {
    input_text: string;
    original_prediction: Record<string, any>;
    user_correction: Record<string, any>;
    feedback_type?: string;
}

export interface FeedbackResponse {
    status: string;
    contribution_count: number;
    message: string;
}

export interface FeedbackStats {
    total_corrections: number;
    buffer_size: number;
    max_buffer_size: number;
    feature_status: 'active' | 'unavailable';
    error?: string;
}

// ============================================================================
// SPATIAL-TEMPORAL CONTEXT TYPES
// ============================================================================

export interface SpatialTemporalRequest {
    item_type: string;
    location: string;
    time?: string;
}

export interface SpatialTemporalResponse {
    plausibility_score: number;
    explanation: string;
    item_location_probability: number;
    item_time_probability: number;
    context: string;
    is_plausible: boolean;
}

export interface SpatialTemporalStats {
    total_validations: number;
    average_plausibility: number;
    common_items: Record<string, number>;
    common_locations: Record<string, number>;
}

// ============================================================================
// XAI (EXPLAINABILITY) TYPES
// ============================================================================

export interface AttentionMapRequest {
    image_path: string;
    target_class?: string;
}

export interface AttentionMapResponse {
    attention_map_url: string;
    top_regions: { x: number; y: number; score: number }[];
    explanation: string;
}

export interface XAIExplainRequest {
    text?: string;
    image_path?: string;
    transcription?: string;
}

export interface XAIExplainResponse {
    explanation: string;
    has_discrepancy: boolean;
    severity?: 'low' | 'medium' | 'high';
    discrepancies?: {
        type: string;
        explanation: string;
    }[];
    enhanced_checks?: Record<string, any>;
}

// ============================================================================
// ENTITY DETECTION TYPES
// ============================================================================

export interface EntityDetectionRequest {
    text: string;
    language?: string;
}

export interface EntityDetectionResponse {
    entities: {
        item_type?: string[];
        color?: string[];
        brand?: string[];
        location?: string[];
        time?: string[];
    };
    raw_entities: { text: string; label: string; start: number; end: number }[];
    confidence: number;
}

export interface EntityType {
    name: string;
    description: string;
    examples: string[];
}
