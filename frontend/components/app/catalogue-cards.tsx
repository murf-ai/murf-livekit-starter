'use client';

import { useEffect, useState } from 'react';
import {
  Clock3Icon,
  HouseIcon,
  LampIcon,
  MapPinIcon,
  MilkIcon,
  PackageIcon,
  SandwichIcon,
  ShirtIcon,
  ShoppingBasketIcon,
  SpeakerIcon,
} from 'lucide-react';

interface CatalogueProduct {
  product_id: string;
  name: string;
  seller: string;
  location: string;
  category: string;
  price_inr: number;
  stock_quantity: number;
  unit: string;
}

interface CatalogueResponse {
  updated_at: string;
  products: CatalogueProduct[];
}

const productVisuals = {
  dairy: { Icon: MilkIcon, className: 'from-sky-100 to-blue-200 text-blue-700' },
  bakery: { Icon: SandwichIcon, className: 'from-amber-100 to-orange-200 text-amber-800' },
  handicrafts: { Icon: LampIcon, className: 'from-orange-100 to-rose-200 text-orange-800' },
  textiles: { Icon: ShirtIcon, className: 'from-fuchsia-100 to-purple-200 text-purple-700' },
  food: { Icon: ShoppingBasketIcon, className: 'from-lime-100 to-emerald-200 text-emerald-700' },
  home: { Icon: HouseIcon, className: 'from-stone-100 to-amber-200 text-stone-700' },
  electronics: { Icon: SpeakerIcon, className: 'from-indigo-100 to-violet-200 text-indigo-700' },
};

function visualFor(category: string) {
  const key = Object.keys(productVisuals).find((item) => category.includes(item));
  return key
    ? productVisuals[key as keyof typeof productVisuals]
    : { Icon: PackageIcon, className: 'from-orange-100 to-amber-200 text-orange-700' };
}

function formatUpdatedAt(value: string) {
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: 'Asia/Kolkata',
  }).format(new Date(value));
}

export function CatalogueCards() {
  const [catalogue, setCatalogue] = useState<CatalogueResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetch('/api/catalogue', { cache: 'no-store', signal: controller.signal })
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.error ?? 'Catalogue unavailable');
        setCatalogue(data);
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === 'AbortError') return;
        setError(reason instanceof Error ? reason.message : 'Catalogue unavailable');
      });
    return () => controller.abort();
  }, []);

  return (
    <section className="mx-auto mt-16 w-full max-w-6xl">
      <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="font-mono text-xs font-bold tracking-[0.18em] text-orange-700 uppercase">
            Local catalogue
          </p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight text-stone-900 dark:text-orange-50">
            Available near you
          </h2>
        </div>
        {catalogue && (
          <p className="flex items-center gap-2 text-xs text-stone-500 dark:text-stone-400">
            <Clock3Icon className="size-4" /> Updated {formatUpdatedAt(catalogue.updated_at)}
          </p>
        )}
      </div>

      {error ? (
        <div className="rounded-3xl border border-dashed border-orange-300 bg-white/75 p-8 text-center shadow-sm dark:border-orange-900 dark:bg-stone-900/75">
          <PackageIcon className="mx-auto size-10 text-orange-600" />
          <p className="mt-4 font-bold text-stone-900 dark:text-stone-100">
            Catalogue temporarily unavailable
          </p>
          <p className="mx-auto mt-2 max-w-xl text-sm text-stone-500 dark:text-stone-400">
            {error}
          </p>
        </div>
      ) : !catalogue ? (
        <div className="h-64 animate-pulse rounded-3xl bg-orange-100/70 dark:bg-stone-800" />
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {catalogue.products.map((product) => {
            const { Icon, className } = visualFor(product.category);
            const available = product.stock_quantity > 0;
            return (
              <article
                key={product.product_id}
                className="overflow-hidden rounded-3xl border border-orange-100 bg-white shadow-md shadow-orange-950/5 transition-transform hover:-translate-y-1 dark:border-stone-800 dark:bg-stone-900"
              >
                <div
                  className={`relative grid h-40 place-items-center bg-gradient-to-br ${className}`}
                >
                  <div className="absolute inset-3 rounded-2xl border border-white/50" />
                  <Icon className="size-20 drop-shadow-sm" strokeWidth={1.35} />
                  <span className="absolute top-4 left-4 rounded-full bg-white/85 px-2.5 py-1 font-mono text-[10px] font-bold text-stone-700 shadow-sm">
                    {product.product_id}
                  </span>
                  <span
                    className={`absolute right-4 bottom-4 rounded-full px-2.5 py-1 text-[10px] font-bold shadow-sm ${
                      available ? 'bg-emerald-700 text-white' : 'bg-stone-800 text-white'
                    }`}
                  >
                    {available ? 'IN STOCK' : 'OUT OF STOCK'}
                  </span>
                </div>

                <div className="p-5">
                  <p className="text-xs font-semibold text-orange-700 dark:text-orange-400">
                    {product.seller}
                  </p>
                  <h3 className="mt-1 min-h-12 text-lg leading-6 font-bold text-stone-900 dark:text-stone-100">
                    {product.name}
                  </h3>
                  <div className="mt-4 flex items-end justify-between gap-3">
                    <div>
                      <p className="text-2xl font-black text-stone-900 dark:text-white">
                        ₹{product.price_inr}
                      </p>
                      <p className="text-xs text-stone-500">per {product.unit}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-stone-800 dark:text-stone-200">
                        {product.stock_quantity} in stock
                      </p>
                      <p className="text-xs text-stone-500">Seller confirmation required</p>
                    </div>
                  </div>
                  <p className="mt-4 flex items-center gap-1.5 border-t border-stone-100 pt-4 text-xs text-stone-500 dark:border-stone-800 dark:text-stone-400">
                    <MapPinIcon className="size-4 shrink-0 text-orange-600" />
                    {product.location}
                  </p>
                  <p className="mt-2 flex items-center gap-1.5 text-[11px] text-stone-400">
                    <Clock3Icon className="size-3.5 shrink-0" />
                    Updated {formatUpdatedAt(catalogue.updated_at)}
                  </p>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
