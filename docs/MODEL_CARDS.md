# Kisan Drishti Model Cards

## AutoML Crop Classification Model
- **Type**: Voting Ensemble (Random Forest + XGBoost)
- **Features**: 70-dimensional multi-temporal spectral + SAR backscatter feature stack
- **Accuracy**: >85% Overall Accuracy, >0.80 Cohen's Kappa (validated on synthetic pilot command area datasets).
- **Target Classes**: Wheat, Rice/Paddy, Cotton, Sugarcane, Maize, Soybean, Groundnut, Mustard/Rapeseed, Vegetables, Fallow/Barren.

## Phenological LSTM Model
- **Type**: Bidirectional PyTorch LSTM Sequence Classifier
- **Features**: Multi-temporal NDVI, EVI, LSWI, VH/VV ratio, and GDD series
- **Output**: seq2seq growth stage classification (emergence, vegetative, flowering, reproductive, maturity, harvest).

## Soil Moisture & Evapotranspiration Deficit Engine
- **Type**: Physics-informed hybrid SEBAL ETa model & Penman-Monteith ETc.
- **Evapotranspiration Actual (ETa)**: Simplified single-pass Surface Energy Balance Algorithm (SEBAL) or fallback MOD16A2 ingestion.
- **Reference ET0**: FAO-56 Penman-Monteith calculation using ground meteorological variables.
