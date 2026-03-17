'use client';

import { useQuery, useMutation } from '@tanstack/react-query';
import { Check, CreditCard, Zap, Sparkles, ArrowLeft, Crown, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';
import { useToast } from '@/providers/toast-provider';

const SUBSCRIPTION_TIERS = {
  free: {
    name: 'Free',
    price: 0,
    features: [
      '10 applications per month',
      'Basic job matching',
      'LinkedIn Easy Apply',
      'Email support',
    ],
  },
  pro: {
    name: 'Pro',
    price: 29,
    features: [
      '100 applications per month',
      'AI-powered job matching',
      'All job platforms',
      'Cold email outreach',
      'Priority support',
    ],
  },
  premium: {
    name: 'Premium',
    price: 79,
    features: [
      'Unlimited applications',
      'Advanced AI matching',
      'All platforms + custom portals',
      'Cold email + follow-ups',
      'Resume optimization',
      'Dedicated support',
    ],
  },
};

export default function BillingSettingsPage() {
  const { addToast } = useToast();

  const { data: subscription, isLoading } = useQuery({
    queryKey: ['subscription'],
    queryFn: () => api.get('/billing/subscription').then((r) => r.data),
  });

  const checkoutMutation = useMutation({
    mutationFn: (priceId: string) => api.post('/billing/checkout', {
      price_id: priceId,
      success_url: `${window.location.origin}/settings/billing?success=true`,
      cancel_url: `${window.location.origin}/settings/billing`,
    }),
    onSuccess: (response) => {
      const url = response.data?.checkout_url || response.data?.url;
      if (url) window.location.href = url;
    },
    onError: () => {
      addToast({ title: 'Failed to start checkout', variant: 'error' });
    },
  });

  const portalMutation = useMutation({
    mutationFn: () => api.post('/billing/portal', {
      return_url: `${window.location.origin}/settings/billing`,
    }),
    onSuccess: (response) => {
      const url = response.data?.portal_url || response.data?.url;
      if (url) window.location.href = url;
    },
    onError: () => {
      addToast({ title: 'Failed to open billing portal', variant: 'error' });
    },
  });

  const currentTier = subscription?.plan || subscription?.subscription_tier || 'free';
  const renewalDate = subscription?.current_period_end
    ? new Date(subscription.current_period_end).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    : null;
  const tierPrice = SUBSCRIPTION_TIERS[currentTier as keyof typeof SUBSCRIPTION_TIERS]?.price || 0;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href="/settings"
          className="p-2 rounded-xl hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">Billing</h1>
          <p className="text-muted-foreground text-sm mt-1">Manage your subscription and billing</p>
        </div>
      </div>

      {/* Current Plan Banner */}
      <div className="relative bg-gradient-to-br from-primary/10 to-transparent rounded-2xl border border-primary/20 p-6 overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl" />
        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-primary/20 flex items-center justify-center">
              <Crown className="w-6 h-6 text-primary" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-foreground capitalize">{currentTier} Plan</h3>
                <span className="text-xs px-2.5 py-1 bg-primary text-primary-foreground rounded-full font-semibold">Current</span>
              </div>
              <p className="text-sm text-muted-foreground">
                {tierPrice > 0 ? `$${tierPrice}/month` : 'Free'}
                {renewalDate ? ` - Renews ${renewalDate}` : ''}
              </p>
            </div>
          </div>
          {currentTier !== 'free' && (
            <button
              onClick={() => portalMutation.mutate()}
              disabled={portalMutation.isPending}
              className="px-4 py-2.5 border border-border rounded-xl text-sm font-medium text-foreground hover:bg-secondary transition-colors"
            >
              {portalMutation.isPending ? 'Loading...' : 'Manage Subscription'}
            </button>
          )}
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.entries(SUBSCRIPTION_TIERS).map(([key, tier]) => {
          const isCurrentPlan = key === currentTier;
          const isPremium = key === 'premium';

          return (
            <div
              key={key}
              className={cn(
                'relative bg-card rounded-2xl border p-6 transition-all',
                isCurrentPlan
                  ? 'border-primary/50 shadow-lg shadow-primary/10'
                  : 'border-border/50 hover:border-border'
              )}
            >
              {isPremium && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="px-3 py-1 bg-gradient-to-r from-amber-400 to-orange-500 text-black text-xs font-bold rounded-full flex items-center gap-1">
                    <Sparkles className="w-3 h-3" /> Popular
                  </span>
                </div>
              )}

              <div className="mb-6">
                <h4 className="text-lg font-semibold text-foreground">{tier.name}</h4>
                <div className="flex items-baseline gap-1 mt-2">
                  <span className="text-3xl font-bold text-foreground">${tier.price}</span>
                  {tier.price > 0 && <span className="text-muted-foreground">/month</span>}
                </div>
              </div>

              <ul className="space-y-3 mb-6">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-2 text-sm text-muted-foreground">
                    <div className="w-5 h-5 rounded-full bg-emerald-400/10 flex items-center justify-center flex-shrink-0">
                      <Check className="w-3 h-3 text-emerald-400" />
                    </div>
                    {feature}
                  </li>
                ))}
              </ul>

              {isCurrentPlan ? (
                <button
                  disabled
                  className="w-full py-2.5 text-sm font-medium bg-secondary text-muted-foreground rounded-xl cursor-not-allowed"
                >
                  Current Plan
                </button>
              ) : key === 'free' ? (
                <button
                  onClick={() => portalMutation.mutate()}
                  className="w-full py-2.5 text-sm font-medium border border-border text-foreground rounded-xl hover:bg-secondary transition-colors"
                >
                  Downgrade
                </button>
              ) : (
                <button
                  onClick={() => checkoutMutation.mutate(key)}
                  disabled={checkoutMutation.isPending}
                  className="w-full py-2.5 text-sm font-medium bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg shadow-primary/20 hover:shadow-primary/30"
                >
                  <Zap className="w-4 h-4" />
                  Upgrade
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Payment Method */}
      <div className="bg-card rounded-2xl border border-border/50 overflow-hidden">
        <div className="p-5 border-b border-border/50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-400/10 flex items-center justify-center">
              <CreditCard className="w-4 h-4 text-cyan-400" />
            </div>
            <h3 className="font-semibold text-foreground">Payment Method</h3>
          </div>
        </div>
        <div className="p-5">
          {subscription?.payment_method ? (
            <div className="flex items-center justify-between p-4 bg-secondary/50 rounded-xl border border-border/50">
              <div className="flex items-center gap-4">
                <div className="w-12 h-8 bg-gradient-to-br from-blue-600 to-blue-800 rounded-md flex items-center justify-center">
                  <span className="text-white text-[10px] font-bold">{(subscription.payment_method.brand || 'CARD').toUpperCase()}</span>
                </div>
                <div>
                  <p className="text-sm font-medium text-foreground">{subscription.payment_method.brand || 'Card'} ending in {subscription.payment_method.last4 || '****'}</p>
                  <p className="text-xs text-muted-foreground">Expires {subscription.payment_method.exp_month}/{subscription.payment_method.exp_year}</p>
                </div>
              </div>
              <button
                onClick={() => portalMutation.mutate()}
                className="px-4 py-2 text-sm font-medium border border-border rounded-xl text-foreground hover:bg-secondary transition-colors"
              >
                Update
              </button>
            </div>
          ) : (
            <div className="text-center py-6 text-muted-foreground">
              <CreditCard className="w-8 h-8 mx-auto mb-2 text-muted-foreground/50" />
              <p className="text-sm">No payment method on file</p>
              {currentTier === 'free' && (
                <p className="text-xs mt-1">Upgrade to a paid plan to add a payment method</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
