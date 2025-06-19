import React from 'react';

// Skeleton loader animation
const shimmer = `relative overflow-hidden before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_1.5s_infinite] before:bg-gradient-to-r before:from-transparent before:via-white/20 before:to-transparent`;

export function SearchResultSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6 space-y-4">
      {/* Title skeleton */}
      <div className={`h-6 bg-gray-200 rounded w-3/4 ${shimmer}`} />
      
      {/* Content skeleton */}
      <div className="space-y-2">
        <div className={`h-4 bg-gray-200 rounded w-full ${shimmer}`} />
        <div className={`h-4 bg-gray-200 rounded w-5/6 ${shimmer}`} />
        <div className={`h-4 bg-gray-200 rounded w-4/6 ${shimmer}`} />
      </div>
      
      {/* Metadata skeleton */}
      <div className="flex gap-4 pt-2">
        <div className={`h-4 bg-gray-200 rounded w-24 ${shimmer}`} />
        <div className={`h-4 bg-gray-200 rounded w-20 ${shimmer}`} />
        <div className={`h-4 bg-gray-200 rounded w-16 ${shimmer}`} />
      </div>
    </div>
  );
}

export function SuggestionSkeleton() {
  return (
    <div className="p-2 space-y-1">
      {[...Array(5)].map((_, i) => (
        <div key={i} className={`h-8 bg-gray-100 rounded ${shimmer}`} />
      ))}
    </div>
  );
}

export function AnswerCardSkeleton() {
  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 space-y-4">
      {/* Header skeleton */}
      <div className="flex items-center gap-2">
        <div className={`h-6 w-6 bg-gray-200 rounded-full ${shimmer}`} />
        <div className={`h-5 bg-gray-200 rounded w-32 ${shimmer}`} />
      </div>
      
      {/* Answer content skeleton */}
      <div className="space-y-3">
        <div className={`h-4 bg-gray-200 rounded w-full ${shimmer}`} />
        <div className={`h-4 bg-gray-200 rounded w-5/6 ${shimmer}`} />
        <div className={`h-4 bg-gray-200 rounded w-4/6 ${shimmer}`} />
        <div className={`h-4 bg-gray-200 rounded w-5/6 ${shimmer}`} />
      </div>
      
      {/* Sources skeleton */}
      <div className="border-t pt-4 space-y-2">
        <div className={`h-4 bg-gray-200 rounded w-24 ${shimmer}`} />
        <div className="flex gap-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className={`h-8 bg-gray-200 rounded-full w-32 ${shimmer}`} />
          ))}
        </div>
      </div>
    </div>
  );
}

export function FilterChipSkeleton() {
  return (
    <div className="flex gap-2">
      {[...Array(4)].map((_, i) => (
        <div key={i} className={`h-8 bg-gray-200 rounded-full w-24 ${shimmer}`} />
      ))}
    </div>
  );
}

// Full page skeleton for initial load
export function SearchPageSkeleton() {
  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Search bar skeleton */}
      <div className={`h-14 bg-gray-200 rounded-lg w-full ${shimmer}`} />
      
      {/* Filters skeleton */}
      <FilterChipSkeleton />
      
      {/* Results skeleton */}
      <div className="grid gap-4">
        <AnswerCardSkeleton />
        {[...Array(3)].map((_, i) => (
          <SearchResultSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}

// Add shimmer animation to global CSS
export const shimmerStyles = `
  @keyframes shimmer {
    to {
      transform: translateX(100%);
    }
  }
`;