'use client'

import { useState } from 'react'
import { getRecommendation, submitFeedback, AccidentScenario, ChatResponse } from '@/lib/api'

const US_STATES = [
  'Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut',
  'Delaware','Florida','Georgia','Hawaii','Idaho','Illinois','Indiana','Iowa',
  'Kansas','Kentucky','Louisiana','Maine','Maryland','Massachusetts','Michigan',
  'Minnesota','Mississippi','Missouri','Montana','Nebraska','Nevada',
  'New Hampshire','New Jersey','New Mexico','New York','North Carolina',
  'North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island',
  'South Carolina','South Dakota','Tennessee','Texas','Utah','Vermont',
  'Virginia','Washington','West Virginia','Wisconsin','Wyoming',
]

const DECISION_STYLES = {
  CLAIM:          { label: 'File a Claim',        bg: 'bg-green-50',  border: 'border-green-400', badge: 'bg-green-600',  icon: '✓' },
  DO_NOT_CLAIM:   { label: "Don't Claim",          bg: 'bg-red-50',    border: 'border-red-400',   badge: 'bg-red-600',    icon: '✕' },
  CONSULT_AGENT:  { label: 'Consult Your Agent',   bg: 'bg-amber-50',  border: 'border-amber-400', badge: 'bg-amber-600',  icon: '!' },
  OUT_OF_SCOPE:   { label: 'Out of Scope',         bg: 'bg-gray-50',   border: 'border-gray-400',  badge: 'bg-gray-600',   icon: '?' },
}

const DEFAULT_FORM: AccidentScenario = {
  repair_cost: 0,
  deductible: 500,
  annual_premium: 1200,
  at_fault: false,
  injuries: false,
  prior_claims_2yr: 0,
  state: 'Texas',
  notes: '',
}

export default function Home() {
  const [form, setForm] = useState<AccidentScenario>(DEFAULT_FORM)
  const [result, setResult] = useState<ChatResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<'thumbs_up' | 'thumbs_down' | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)
    setFeedback(null)
    try {
      const data = await getRecommendation(form)
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const handleFeedback = async (rating: 'thumbs_up' | 'thumbs_down') => {
    if (!result || feedback) return
    setFeedback(rating)
    await submitFeedback(result.user_id, result.session_id, rating)
  }

  const rec = result?.recommendation
  const style = rec ? DECISION_STYLES[rec.decision] : null

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white text-sm font-bold">A</div>
          <div>
            <h1 className="text-lg font-semibold text-slate-900">Post-Accident Guidance Assistant</h1>
            <p className="text-xs text-slate-500">AI-powered claim vs. no-claim decision engine</p>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

          {/* Left: Form */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <h2 className="text-base font-semibold text-slate-800 mb-1">Accident Details</h2>
            <p className="text-sm text-slate-500 mb-6">Fill in what you know — we&apos;ll handle the rest.</p>

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Financial fields */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Repair Cost ($)</label>
                  <input
                    type="number" min="0" step="1" required
                    value={form.repair_cost || ''}
                    onChange={e => setForm(f => ({ ...f, repair_cost: parseFloat(e.target.value) || 0 }))}
                    className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g. 2500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Deductible ($)</label>
                  <input
                    type="number" min="0" step="1" required
                    value={form.deductible || ''}
                    onChange={e => setForm(f => ({ ...f, deductible: parseFloat(e.target.value) || 0 }))}
                    className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g. 500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Annual Premium ($)</label>
                <input
                  type="number" min="0" step="1" required
                  value={form.annual_premium || ''}
                  onChange={e => setForm(f => ({ ...f, annual_premium: parseFloat(e.target.value) || 0 }))}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g. 1200"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">State of Accident</label>
                <select
                  value={form.state}
                  onChange={e => setForm(f => ({ ...f, state: e.target.value }))}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                >
                  {US_STATES.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Prior Claims (last 2 years)</label>
                <select
                  value={form.prior_claims_2yr}
                  onChange={e => setForm(f => ({ ...f, prior_claims_2yr: parseInt(e.target.value) }))}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                >
                  {[0,1,2,3].map(n => <option key={n} value={n}>{n}</option>)}
                </select>
              </div>

              {/* Toggles */}
              <div className="space-y-3">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.at_fault}
                    onChange={e => setForm(f => ({ ...f, at_fault: e.target.checked }))}
                    className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-slate-700">I was at fault</span>
                </label>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.injuries}
                    onChange={e => setForm(f => ({ ...f, injuries: e.target.checked }))}
                    className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-slate-700">Injuries were involved</span>
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Additional Notes <span className="text-slate-400 font-normal">(optional)</span></label>
                <textarea
                  rows={3}
                  value={form.notes}
                  onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  placeholder="e.g. Uber driver, classic car, other driver fled scene..."
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-2.5 rounded-lg text-sm transition-colors"
              >
                {loading ? 'Analyzing...' : 'Get Recommendation'}
              </button>
            </form>

            {error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                {error}
              </div>
            )}
          </div>

          {/* Right: Results */}
          <div>
            {!result && !loading && (
              <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 py-24">
                <div className="text-5xl mb-4">🚗</div>
                <p className="text-sm">Your recommendation will appear here</p>
              </div>
            )}

            {loading && (
              <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 py-24">
                <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
                <p className="text-sm">Analyzing your scenario...</p>
              </div>
            )}

            {result && rec && style && (
              <div className={`rounded-xl border-2 ${style.border} ${style.bg} p-6 space-y-5`}>
                {/* Decision header */}
                <div className="flex items-center gap-3">
                  <span className={`${style.badge} text-white text-xl font-bold w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0`}>
                    {style.icon}
                  </span>
                  <div>
                    <p className="text-xs text-slate-500 uppercase tracking-wide font-medium">Recommendation</p>
                    <h3 className="text-xl font-bold text-slate-900">{style.label}</h3>
                  </div>
                  <div className="ml-auto text-right">
                    <p className="text-xs text-slate-500">Confidence</p>
                    <p className="text-sm font-semibold text-slate-700">{rec.confidence} ({Math.round(rec.confidence_score * 100)}%)</p>
                  </div>
                </div>

                {/* Summary */}
                <p className="text-sm text-slate-700 font-medium">{rec.summary}</p>

                {/* Financial breakdown */}
                <div className="bg-white rounded-lg p-4 border border-slate-200">
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Financial Breakdown</p>
                  <p className="text-sm text-slate-700">{rec.financial_breakdown}</p>
                </div>

                {/* Key factors */}
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Key Factors</p>
                  <ul className="space-y-1">
                    {rec.key_factors.map((f, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                        <span className="text-slate-400 mt-0.5">•</span>
                        {f}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Reasoning */}
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Reasoning</p>
                  <p className="text-sm text-slate-700 leading-relaxed">{rec.reasoning}</p>
                </div>

                {/* Next steps */}
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Next Steps</p>
                  <ol className="space-y-1">
                    {rec.next_steps.map((step, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                        <span className="text-slate-400 font-medium mt-0.5">{i + 1}.</span>
                        {step}
                      </li>
                    ))}
                  </ol>
                </div>

                {/* Disclaimer */}
                <p className="text-xs text-slate-400 italic border-t border-slate-200 pt-4">{rec.disclaimer}</p>

                {/* Feedback */}
                <div className="border-t border-slate-200 pt-4">
                  <p className="text-xs text-slate-500 mb-2">Was this helpful?</p>
                  {feedback ? (
                    <p className="text-sm text-slate-600">Thanks for your feedback!</p>
                  ) : (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleFeedback('thumbs_up')}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 text-sm text-slate-600 hover:bg-white transition-colors"
                      >
                        👍 Yes
                      </button>
                      <button
                        onClick={() => handleFeedback('thumbs_down')}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 text-sm text-slate-600 hover:bg-white transition-colors"
                      >
                        👎 No
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
