# Quick Start ML/DL Implementation (30 Minutes)

Get all ML features working in just 30 minutes.

---

## STEP 1: Verify Files Exist (2 minutes)

Check that these files are in your project:
- `ml_quickstart.py` (the ML module - copy to project if missing)
- Your existing `app.py`
- Your existing `database.py`

---

## STEP 2: Install Dependencies (5 minutes)

Open terminal in your project folder and run:

```powershell
pip install xgboost prophet transformers torch --upgrade
```

Or add to requirements.txt and run:

```powershell
pip install -r requirements.txt
```

Verify with:
```powershell
python -c "from ml_quickstart import FastChurnPredictor; print('Success')"
```

---

## STEP 3: Add to app.py (10 minutes)

Add this import at the TOP of your `app.py` file:

```python
from ml_quickstart import get_quick_insights
```

Find your Dashboard page code (search for `page == "Dashboard"`), and add this section at the END:

```python
if page == "Dashboard":
    # ... your existing dashboard code ...
    
    # ADD THIS NEW SECTION AT THE END
    st.divider()
    st.subheader("ML-Powered Insights")
    
    try:
        insights = get_quick_insights()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            churn_count = len(insights['churn_risks'])
            st.metric("High-Risk Customers", churn_count, "Churn Alert")
        
        with col2:
            metrics = insights['metrics']
            st.metric("Win Rate", f"{metrics['win_rate']:.1f}%")
        
        with col3:
            trends = insights['trends']
            st.metric("Revenue Trend", trends['trend'], f"{trends['trend_percent']:.1f}%")
        
        # Show more details in expandable sections
        with st.expander("View Details"):
            tab1, tab2, tab3 = st.tabs(["Churn Risks", "Trends", "Deals"])
            
            with tab1:
                if insights['churn_risks']:
                    churn_df = pd.DataFrame(insights['churn_risks'])
                    st.dataframe(churn_df[['customer_name', 'risk', 'reason']], use_container_width=True)
                else:
                    st.success("No high-risk customers")
            
            with tab2:
                trends = insights['trends']
                st.write(f"Overall: {trends['trend']} {trends['trend_percent']:.1f}%")
                st.write(f"Month-to-Month: {trends['mom_change']:.1f}%")
            
            with tab3:
                deals = insights['deals']
                st.write(f"Average Deal: ${deals['average_deal']:,.0f}")
                st.write(f"Total Revenue: ${deals['total_revenue']:,.0f}")
    
    except Exception as e:
        st.warning(f"ML features temporarily unavailable: {str(e)}")
```

---

## STEP 4: Test Dashboard (5 minutes)

1. Save your `app.py`
2. Run: `streamlit run app.py`
3. Go to Dashboard page
4. Scroll down to "ML-Powered Insights"
5. Should see 3 new metric cards
6. Verify no errors appear

If you see errors, check:
- Did you copy `ml_quickstart.py` to your project folder?
- Did you install dependencies: `pip install -r requirements.txt`?
- Check the terminal for specific error messages

---

## STEP 5 (Optional): Add New ML Analytics Page (8 minutes)

If you want a dedicated ML page with advanced features, add this to your page selection logic:

```python
# Find where you define pages (usually something like: pages = ["Dashboard", "Manage Quotes", ...])
# Add "ML Analytics" to that list

# Then add this code at the bottom of your app.py, before main()

if page == "ML Analytics":
    st.title("ML Analytics")
    
    from ml_quickstart import (
        FastChurnPredictor, QuickSegmentation, QuickAnomalyDetector,
        QuickRecommender, QuickHealthScore
    )
    
    tab1, tab2, tab3 = st.tabs(["Churn", "Segments", "Health"])
    
    with tab1:
        st.subheader("Churn Risk Analysis")
        predictor = FastChurnPredictor()
        customers = db.get_customers()
        
        churn_data = []
        for customer in customers:
            pred = predictor.predict_churn(customer['id'])
            churn_data.append({
                "Customer": customer['name'],
                "Risk %": pred['risk'],
                "Status": pred['reason']
            })
        
        churn_df = pd.DataFrame(churn_data)
        st.dataframe(churn_df.sort_values("Risk %", ascending=False), use_container_width=True)
    
    with tab2:
        st.subheader("Customer Segments")
        seg = QuickSegmentation()
        segments = seg.segment_all()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("VIP", segments['VIP']['size'])
        with col2:
            st.metric("Growth", segments['Growth']['size'])
        with col3:
            st.metric("Active", segments['Active']['size'])
        with col4:
            st.metric("Inactive", segments['Inactive']['size'])
        
        selected = st.selectbox("View Segment:", list(segments.keys()))
        st.write(f"Action: {segments[selected]['action']}")
    
    with tab3:
        st.subheader("Customer Health")
        health_calc = QuickHealthScore()
        customers = db.get_customers()
        
        health_data = []
        for customer in customers:
            health = health_calc.get_health_score(customer['id'])
            health_data.append({
                "Customer": customer['name'],
                "Score": health['score'],
                "Status": health['status']
            })
        
        health_df = pd.DataFrame(health_data)
        st.dataframe(health_df.sort_values("Score", ascending=False), use_container_width=True)
```

---

## DONE! You Now Have:

After these 30 minutes, you have:

✓ 8 new ML features working
✓ Dashboard with ML insights
✓ (Optional) New ML Analytics page
✓ Churn predictions
✓ Customer segments
✓ Deal analysis
✓ Revenue trends
✓ All metrics calculated automatically

---

## Testing with Sample Data

If you don't have enough data, create test quotes:

1. Go to "Batch Operations" page
2. Download the Quotes template
3. Create 50+ sample quotes with different statuses
4. Import them
5. Return to Dashboard/ML Analytics
6. All features will show real data

---

## Troubleshooting Quick Fixes

### Problem: "ModuleNotFoundError: No module named 'ml_quickstart'"
Fix: Make sure `ml_quickstart.py` is in the same folder as `app.py`

### Problem: "KeyError" or "AttributeError"
Fix: Make sure database has some quotes. Run Batch Operations first.

### Problem: All metrics show 0 or empty
Fix: Normal if no data. Create test data via Batch Operations.

### Problem: App crashes on Dashboard
Fix: Wrap code in try-except (see Step 4 code - it has error handling)

### Problem: Nothing appears
Fix: 
1. Save app.py
2. Stop streamlit (Ctrl+C)
3. Run again: `streamlit run app.py`

---

## What Each Feature Does

1. **High-Risk Customers** - Shows customers likely to churn
2. **Win Rate** - Percentage of quotes accepted
3. **Revenue Trend** - Is revenue going up or down?
4. **Churn Risks Details** - Which customers are at risk and why
5. **Trends** - Month-over-month changes
6. **Deal Analysis** - Average, median, min/max quote amounts

---

## Next Steps (After You Get This Working)

1. Monitor the metrics for a few days
2. Check which features are most useful
3. Read `ML_DL_IMPLEMENTATION_GUIDE.md` for more options
4. Add more advanced features from there
5. Consider training models (Week 2 features)

---

## One-Line Test

Run this to verify everything works:

```python
python -c "from ml_quickstart import get_quick_insights; import json; print(json.dumps(get_quick_insights(), indent=2, default=str))"
```

Should print all insights without errors.

---

## Performance Notes

- First time: might be slightly slow (1-2 seconds)
- Subsequent times: should be instant (thanks to caching)
- With 1000+ quotes: might take 2-3 seconds
- This is normal and expected

---

## That's It!

You now have professional ML/DL analytics running in your Quote Builder Pro system.

Enjoy the new insights and feel free to explore the advanced features in the full guide.

For questions or issues, refer to:
- `ML_DL_IMPLEMENTATION_GUIDE.md` - Full documentation
- `ML_IMPLEMENTATION_CHECKLIST.md` - Step-by-step guide
- `ML_STREAMLIT_INTEGRATION.md` - Integration examples