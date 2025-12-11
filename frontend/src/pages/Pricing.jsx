import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { CheckCircle2, Crown, ShieldCheck, Zap, ArrowLeft } from "lucide-react";

const plans = [
  {
    name: "Basic",
    price: "Free",
    badge: "Start here",
    planValue: "basic",
    features: [
      "Unlimited searches (rate limited)",
      "Save searches locally",
      "Export to PDF/Excel",
      "Access to citation mesh viewer",
    ],
    cta: "Start for Free",
    accent: "border-gray-200",
    highlight: false,
  },
  {
    name: "Premium",
    price: "$50",
    badge: "Most popular",
    planValue: "premium",
    features: [
      "Access to paid research papers",
      "Priority search throughput",
      "Cloud saved searches",
      "Advanced filters & sorting",
      "Enhanced export (metadata sheets)",
      "Email support",
    ],
    cta: "Get Premium",
    accent: "border-gray-200",
    highlight: false,
  },
  {
    name: "Advanced",
    price: "$100",
    badge: "For teams",
    planValue: "advanced",
    features: [
      "All Premium features",
      "Team seats & collaboration",
      "API access & higher limits",
      "Priority support",
      "Custom onboarding",
    ],
    cta: "Get Advanced",
    accent: "border-gray-200",
    highlight: false,
  },
];

export default function Pricing() {
  const navigate = useNavigate();
  const [selectedPlan, setSelectedPlan] = useState("basic");

  const goToPayment = (planValue) => {
    if (planValue === "basic") {
      navigate("/");
    } else {
      navigate(`/payment?plan=${planValue}`);
    }
  };

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-5xl mx-auto px-4 py-12">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-black mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-black text-white text-sm font-medium mb-3">
            <Crown className="w-4 h-4" />
            Choose your plan
          </div>
          <h1 className="text-3xl md:text-4xl font-semibold text-black mb-3">
            Simple pricing for every researcher
          </h1>
          <p className="text-gray-600 text-lg">
            Start free, upgrade when you need more power.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {plans.map((plan) => {
            const isActive = selectedPlan === plan.planValue;
            return (
              <div
                key={plan.name}
                onClick={() => setSelectedPlan(plan.planValue)}
                className={`border rounded-2xl p-6 flex flex-col cursor-pointer transition-colors ${
                  isActive ? "border-black shadow-md bg-gray-50" : "border-gray-200 bg-white hover:border-black/50"
                }`}
              >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm text-gray-500">{plan.badge}</p>
                  <h2 className="text-xl font-semibold text-black">
                    {plan.name}
                  </h2>
                </div>
                {plan.highlight ? (
                  <ShieldCheck className="w-6 h-6 text-black" />
                ) : (
                  <Zap className="w-6 h-6 text-gray-400" />
                )}
              </div>

              <div className="mb-6">
                <span className="text-3xl font-semibold text-black">
                  {plan.price}
                </span>
                {plan.price !== "Free" && (
                  <span className="text-gray-500 text-sm"> / month</span>
                )}
              </div>

              <ul className="space-y-3 mb-6">
                {plan.features.map((feat) => (
                  <li key={feat} className="flex items-center gap-2 text-sm text-gray-700">
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                    <span>{feat}</span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => goToPayment(plan.planValue)}
                className={`w-full py-2.5 rounded-full text-sm font-semibold transition-colors ${
                  isActive
                    ? "bg-black text-white hover:bg-gray-800"
                    : "border border-gray-300 text-black hover:bg-gray-100"
                }`}
              >
                {plan.cta}
              </button>
            </div>
            );
          })}
        </div>

        
      </div>
    </div>
  );
}

