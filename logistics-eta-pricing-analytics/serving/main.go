// Real-time ETA + pricing serving layer.
//
// Reads the current demand index for a region (from a cache populated by
// the Databricks streaming job) and returns a predicted ETA and surge
// multiplier for a trip request. Go is used here rather than Python
// because this sits on the request hot path (target p99 < 50ms), the
// same reason Uber and DoorDash run their pricing/dispatch services in
// statically-typed, low-GC-pause languages rather than the analytics
// stack itself.
package main

import (
	"encoding/json"
	"log"
	"math"
	"net/http"
)

// RegionDemand would normally be read from Redis, populated by a
// consumer of the same Kafka topic the Databricks Structured Streaming
// job reads from.
var regionDemand = map[string]float64{
	"North":    1.05,
	"South":    1.10,
	"East":     1.30,
	"West":     0.95,
	"Downtown": 1.45,
}

type quoteRequest struct {
	Region     string  `json:"region"`
	DistanceKm float64 `json:"distance_km"`
}

type quoteResponse struct {
	Region            string  `json:"region"`
	PredictedETAMin   float64 `json:"predicted_eta_minutes"`
	SurgeMultiplier   float64 `json:"surge_multiplier"`
	BaseFareUSD       float64 `json:"base_fare_usd"`
	FinalFareUSD      float64 `json:"final_fare_usd"`
}

func demandIndex(region string) float64 {
	if v, ok := regionDemand[region]; ok {
		return v
	}
	return 1.0
}

func surgeMultiplier(demand float64) float64 {
	m := 1 + (demand-1)*0.6
	if m < 1.0 {
		m = 1.0
	}
	if m > 2.5 {
		m = 2.5
	}
	return math.Round(m*100) / 100
}

func handleQuote(w http.ResponseWriter, r *http.Request) {
	var req quoteRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid request body", http.StatusBadRequest)
		return
	}
	if req.DistanceKm <= 0 {
		http.Error(w, "distance_km must be positive", http.StatusBadRequest)
		return
	}

	demand := demandIndex(req.Region)
	surge := surgeMultiplier(demand)
	predictedETA := math.Round(req.DistanceKm*2.6*10) / 10
	baseFare := 4.5 + req.DistanceKm*1.35
	finalFare := math.Round(baseFare*surge*100) / 100

	resp := quoteResponse{
		Region:          req.Region,
		PredictedETAMin: predictedETA,
		SurgeMultiplier: surge,
		BaseFareUSD:     math.Round(baseFare*100) / 100,
		FinalFareUSD:    finalFare,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func main() {
	http.HandleFunc("/v1/quote", handleQuote)
	log.Println("eta-pricing service listening on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
