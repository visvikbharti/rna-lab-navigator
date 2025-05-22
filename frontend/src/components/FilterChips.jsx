const FilterChips = ({ selected, onChange }) => {
  const filters = [
    { id: 'all', label: 'All' },
    { id: 'protocol', label: 'Protocols' },
    { id: 'paper', label: 'Papers' },
    { id: 'thesis', label: 'Theses' },
  ];

  return (
    <div className="flex flex-wrap gap-2 mb-4">
      {filters.map((filter) => (
        <button
          key={filter.id}
          className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
            selected === filter.id
              ? 'bg-primary-600 text-white'
              : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
          }`}
          onClick={() => onChange(filter.id)}
        >
          {filter.label}
        </button>
      ))}
    </div>
  );
};

export default FilterChips;