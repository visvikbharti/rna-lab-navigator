import { motion } from 'framer-motion';
import { BookOpenIcon, DocumentTextIcon, BeakerIcon, AcademicCapIcon } from '@heroicons/react/24/outline';

const FilterChips = ({ selected, onChange }) => {
  const filters = [
    { id: 'all', label: 'All Documents', icon: BookOpenIcon, color: 'from-blue-500 to-purple-500' },
    { id: 'protocol', label: 'Protocols', icon: BeakerIcon, color: 'from-green-500 to-teal-500' },
    { id: 'paper', label: 'Papers', icon: DocumentTextIcon, color: 'from-orange-500 to-red-500' },
    { id: 'thesis', label: 'Theses', icon: AcademicCapIcon, color: 'from-purple-500 to-pink-500' },
  ];

  return (
    <div className="flex flex-wrap gap-3 justify-center">
      {filters.map((filter, index) => {
        const Icon = filter.icon;
        const isSelected = selected === filter.id;
        
        return (
          <motion.button
            key={filter.id}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ 
              duration: 0.3,
              delay: index * 0.05 
            }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={`
              relative px-5 py-2.5 rounded-full text-sm font-medium 
              backdrop-blur-md border transition-all duration-300
              flex items-center gap-2 group
              ${isSelected
                ? 'bg-gradient-to-r ' + filter.color + ' text-white border-white/30 shadow-lg'
                : 'bg-white/10 text-gray-300 hover:bg-white/20 border-white/20 hover:border-white/30'
              }
            `}
            onClick={() => onChange(filter.id)}
          >
            <Icon className={`w-4 h-4 ${isSelected ? 'text-white' : 'text-gray-400 group-hover:text-white'}`} />
            <span>{filter.label}</span>
            
            {isSelected && (
              <motion.div
                layoutId="activeFilter"
                className="absolute inset-0 bg-gradient-to-r from-white/20 to-white/10 rounded-full"
                style={{ zIndex: -1 }}
              />
            )}
          </motion.button>
        );
      })}
    </div>
  );
};

export default FilterChips;