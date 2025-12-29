# Phase 2 XAI API Endpoints
# Add these to app.py after existing spatial-temporal endpoints


@app.post("/api/xai/attention", response_model=AttentionMapResponse)
async def generate_attention_heatmap(
    image_file: UploadFile = File(...),
    text: str = Form(...),
    api_key: APIKey = Depends(get_api_key),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Generate attention heatmap for image-text pair.
    Shows which image regions the model focuses on when matching text.
    
    Phase 2: XAI Attention Visualization
    """
    try:
        from src.cross_modal.attention_visualizer import get_attention_visualizer
        from src.image.clip_validator import get_clip_validator
        
        # Validate and save image
        if not validate_file_type(image_file, ALLOWED_IMAGE_TYPES):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image type. Allowed: {ALLOWED_IMAGE_TYPES}"
            )
        
        image_path = save_uploaded_file(image_file)
        background_tasks.add_task(cleanup_file, image_path)
        
        # Get CLIP model
        clip_validator = get_clip_validator()
        if not clip_validator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="CLIP model unavailable"
            )
        
        # Generate attention map
        visualizer = get_attention_visualizer()
        result = visualizer.generate_attention_map(
            image_path=image_path,
            text=text,
            clip_model=clip_validator.model
        )
        
        # Convert file path to URL if heatmap generated
        if result.get("heatmap_path"):
            # Make it accessible via /static/ endpoint
            heatmap_filename = os.path.basename(result["heatmap_path"])
            result["heatmap_url"] = f"/static/heatmaps/{heatmap_filename}"
            # Schedule heatmap cleanup
            background_tasks.add_task(cleanup_file, result["heatmap_path"])
        
        logger.info(f"Attention heatmap generated for text: '{text[:50]}...'")
        
        return AttentionMapResponse(**result)
        
    except Exception as e:
        logger.error(f"Attention heatmap generation failed: {e}")
        return AttentionMapResponse(
            explanation=f"Attention analysis failed: {str(e)}",
            error=str(e)
        )


@app.post("/api/xai/explain-enhanced")
async def get_enhanced_xai_explanation(
    request: EnhancedXAIRequest,
    api_key: APIKey = Depends(get_api_key)
):
    """
    Get comprehensive XAI explanation with multi-dimensional discrepancy detection.
    
    Phase 2: Enhanced XAI with brand, location, and condition checks.
    """
    try:
        from src.cross_modal.xai_explainer import XAIExplainer
        from src.cross_modal.enhanced_discrepancies import (
            check_brand_mismatch,
            check_location_consistency,
            check_condition_mismatch
        )
        
        explainer = XAIExplainer()
        
        # Get basic explanation
        base_explanation = explainer.generate_explanation(
            image_result=request.get("image_result"),
            text_result=request.get("text_result"),
            voice_result=request.get("voice_result")
        )
        
        # Add enhanced discrepancy checks if requested
        if request.include_discrepancies:
            enhanced_checks = {}
            
            # Brand mismatch
            brand_check = check_brand_mismatch(
                request.get("image_result"),
                request.get("text_result")
            )
            if brand_check.get("has_mismatch"):
                enhanced_checks["brand_mismatch"] = brand_check
            
            # Location consistency (text vs voice)
            location_check = check_location_consistency(
                request.get("text_result"),
                request.get("voice_result")
            )
            if location_check.get("has_mismatch"):
                enhanced_checks["location_inconsistency"] = location_check
            
            # Condition mismatch
            condition_check = check_condition_mismatch(
                request.get("image_result"),
                request.get("text_result")
            )
            if condition_check.get("has_mismatch"):
                enhanced_checks["condition_mismatch"] = condition_check
            
            if enhanced_checks:
                base_explanation["enhanced_checks"] = enhanced_checks
                base_explanation["has_discrepancy"] = True
        
        return base_explanation
        
    except Exception as e:
        logger.error(f"Enhanced XAI explanation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"XAI explanation failed: {str(e)}"
        )


# Static file serving for heatmaps (add to app setup)
# from fastapi.staticfiles import StaticFiles
# app.mount("/static", StaticFiles(directory="uploads"), name="static")
