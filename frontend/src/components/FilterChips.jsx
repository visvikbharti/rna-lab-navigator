import { motion } from 'framer-motion';
import { useAnimation } from '../contexts/AnimationContext';

const FilterChips = ({ selected, onChange }) => {
  const { transitionClasses, scaleIn } = useAnimation();
  
  const filters = [
    { id: 'all', label: 'All', icon: '📚' },
    { id: 'protocol', label: 'Protocols', icon: '🧪' },
    { id: 'paper', label: 'Papers', icon: '📄' },
    { id: 'thesis', label: 'Theses', icon: '📖' },
  ];

  return (
    <div className="flex flex-wrap gap-2 mb-4">
      {filters.map((filter, index) => (
        <motion.button
          key={filter.id}
          variants={scaleIn}
          initial="initial"
          animate="animate"
          transition={{ delay: index * 0.05 }}
          className={`px-4 py-2 rounded-xl text-sm font-medium backdrop-blur-md border ${transitionClasses.fast} ${
            selected === filter.id
              ? 'bg-gradient-to-r from-primary-600/90 to-primary-700/90 text-white border-primary-500/50 shadow-lg'
              : 'bg-white/60 dark:bg-gray-800/60 text-gray-800 dark:text-gray-200 hover:bg-white/80 dark:hover:bg-gray-800/80 border-gray-200/50 dark:border-gray-700/50'
          }`}
          onClick={() => onChange(filter.id)}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <span className="flex items-center gap-2">
            <span>{filter.icon}</span>
            {filter.label}
          </span>
        </motion.button>
      ))}
    </div>
  );
};

export default FilterChips;