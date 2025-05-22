/**
 * Enhanced Components Demo - RNA Lab Navigator
 * Demonstration of the colossal.com-inspired component library
 * Phase 1: Foundation Setup
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  BeakerIcon, 
  DocumentIcon, 
  MagnifyingGlassIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  HeartIcon,
  StarIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

import {
  Button,
  ButtonGroup,
  IconButton,
  FloatingActionButton,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  FeatureCard,
  StatCard,
  Input,
  SearchInput,
  Textarea,
  FormGroup,
  Loading,
  Spinner,
  RNAHelixSpinner,
  PulseLoader,
  DotsLoader,
  ProgressLoader,
  Skeleton,
  useAnimation
} from './index';

/**
 * Enhanced Components Demo
 */
const EnhancedComponentsDemo = () => {
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(45);
  const { reducedMotion } = useAnimation();

  const handleDemoAction = (action) => {
    toast.success(`${action} action triggered!`);
  };

  const handleLoadingDemo = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 3000);
  };

  const handleProgressDemo = () => {
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          toast.success('Progress completed!');
          return 0;
        }
        return prev + 10;
      });
    }, 500);
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <div className="min-h-screen bg-rna-platinum py-12">
      <div className="container mx-auto px-4 max-w-7xl">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="space-y-12"
        >
          {/* Header */}
          <motion.div variants={itemVariants} className="text-center">
            <h1 className="text-hero font-bold text-gradient mb-4">
              Enhanced Component Library
            </h1>
            <p className="text-h4 text-rna-graphite max-w-2xl mx-auto">
              Colossal.com-inspired components for the RNA Lab Navigator
            </p>
          </motion.div>

          {/* Buttons Section */}
          <motion.section variants={itemVariants}>
            <Card className="p-8">
              <CardHeader>
                <CardTitle>Button Components</CardTitle>
                <CardDescription>
                  Interactive buttons with animations and various styles
                </CardDescription>
              </CardHeader>
              
              <CardContent className="space-y-6">
                {/* Primary Buttons */}
                <div className="space-y-4">
                  <h4 className="text-h4 font-semibold text-rna-charcoal">Primary Buttons</h4>
                  <div className="flex flex-wrap gap-4">
                    <Button onClick={() => handleDemoAction('Primary')}>
                      Primary Button
                    </Button>
                    <Button 
                      loading={loading} 
                      onClick={handleLoadingDemo}
                    >
                      {loading ? 'Loading...' : 'Click for Loading'}
                    </Button>
                    <Button shimmer onClick={() => handleDemoAction('Shimmer')}>
                      Shimmer Effect
                    </Button>
                    <Button 
                      leftIcon={<BeakerIcon className="w-5 h-5" />}
                      onClick={() => handleDemoAction('Icon')}
                    >
                      With Icon
                    </Button>
                  </div>
                </div>

                {/* Button Variants */}
                <div className="space-y-4">
                  <h4 className="text-h4 font-semibold text-rna-charcoal">Button Variants</h4>
                  <div className="flex flex-wrap gap-4">
                    <Button variant="secondary" onClick={() => handleDemoAction('Secondary')}>
                      Secondary
                    </Button>
                    <Button variant="ghost" onClick={() => handleDemoAction('Ghost')}>
                      Ghost
                    </Button>
                    <Button variant="outline" onClick={() => handleDemoAction('Outline')}>
                      Outline
                    </Button>
                    <Button variant="success" onClick={() => handleDemoAction('Success')}>
                      Success
                    </Button>
                    <Button variant="danger" onClick={() => handleDemoAction('Danger')}>
                      Danger
                    </Button>
                  </div>
                </div>

                {/* Button Sizes */}
                <div className="space-y-4">
                  <h4 className="text-h4 font-semibold text-rna-charcoal">Button Sizes</h4>
                  <div className="flex flex-wrap items-center gap-4">
                    <Button size="sm" onClick={() => handleDemoAction('Small')}>
                      Small
                    </Button>
                    <Button size="md" onClick={() => handleDemoAction('Medium')}>
                      Medium
                    </Button>
                    <Button size="lg" onClick={() => handleDemoAction('Large')}>
                      Large
                    </Button>
                    <Button size="xl" onClick={() => handleDemoAction('Extra Large')}>
                      Extra Large
                    </Button>
                  </div>
                </div>

                {/* Button Group */}
                <div className="space-y-4">
                  <h4 className="text-h4 font-semibold text-rna-charcoal">Button Group</h4>
                  <ButtonGroup>
                    <Button variant="outline">First</Button>
                    <Button variant="outline">Second</Button>
                    <Button variant="outline">Third</Button>
                  </ButtonGroup>
                </div>

                {/* Icon Buttons */}
                <div className="space-y-4">
                  <h4 className="text-h4 font-semibold text-rna-charcoal">Icon Buttons</h4>
                  <div className="flex gap-4">
                    <IconButton
                      icon={<HeartIcon className="w-5 h-5" />}
                      aria-label="Like"
                      onClick={() => handleDemoAction('Like')}
                    />
                    <IconButton
                      icon={<StarIcon className="w-5 h-5" />}
                      aria-label="Favorite"
                      variant="secondary"
                      onClick={() => handleDemoAction('Favorite')}
                    />
                    <IconButton
                      icon={<CheckCircleIcon className="w-5 h-5" />}
                      aria-label="Complete"
                      variant="success"
                      onClick={() => handleDemoAction('Complete')}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.section>

          {/* Cards Section */}
          <motion.section variants={itemVariants}>
            <Card className="p-8">
              <CardHeader>
                <CardTitle>Card Components</CardTitle>
                <CardDescription>
                  Flexible card layouts with interactive states
                </CardDescription>
              </CardHeader>
              
              <CardContent className="space-y-8">
                {/* Feature Cards */}
                <div className="space-y-4">
                  <h4 className="text-h4 font-semibold text-rna-charcoal">Feature Cards</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <FeatureCard
                      icon={<BeakerIcon className="w-full h-full" />}
                      title="Lab Protocols"
                      description="Access standardized protocols for RNA research and analysis"
                      onClick={() => handleDemoAction('Protocols')}
                    />
                    <FeatureCard
                      icon={<DocumentIcon className="w-full h-full" />}
                      title="Research Papers"
                      description="Search through curated research papers and publications"
                      onClick={() => handleDemoAction('Papers')}
                    />
                    <FeatureCard
                      icon={<MagnifyingGlassIcon className="w-full h-full" />}
                      title="Smart Search"
                      description="AI-powered search with contextual understanding"
                      onClick={() => handleDemoAction('Search')}
                    />
                  </div>
                </div>

                {/* Stat Cards */}
                <div className="space-y-4">
                  <h4 className="text-h4 font-semibold text-rna-charcoal">Stat Cards</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <StatCard
                      label="Total Documents"
                      value="1,234"
                      change="+12% from last month"
                      changeType="positive"
                      icon={<DocumentIcon className="w-full h-full" />}
                    />
                    <StatCard
                      label="Active Users"
                      value="89"
                      change="+5% from last week"
                      changeType="positive"
                      icon={<ChartBarIcon className="w-full h-full" />}
                    />
                    <StatCard
                      label="Search Accuracy"
                      value="94.2%"
                      change="-2% from last month"
                      changeType="negative"
                      icon={<ShieldCheckIcon className="w-full h-full" />}
                    />
                  </div>
                </div>

                {/* Card Variants */}
                <div className="space-y-4">
                  <h4 className="text-h4 font-semibold text-rna-charcoal">Card Variants</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card variant="glass" className="p-6">
                      <CardTitle className="mb-2">Glass Card</CardTitle>
                      <CardDescription>
                        Glass morphism effect with backdrop blur
                      </CardDescription>
                    </Card>
                    <Card variant="gradient" className="p-6">
                      <CardTitle className="mb-2">Gradient Card</CardTitle>
                      <CardDescription>
                        Subtle gradient background for visual depth
                      </CardDescription>
                    </Card>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.section>

          {/* Input Components Section */}
          <motion.section variants={itemVariants}>
            <Card className="p-8">
              <CardHeader>
                <CardTitle>Input Components</CardTitle>
                <CardDescription>
                  Form inputs with enhanced interactions and validation
                </CardDescription>
              </CardHeader>
              
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <FormGroup>
                    <Input
                      label="Standard Input"
                      placeholder="Enter some text..."
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      helperText="This is a standard input field"
                    />
                  </FormGroup>

                  <FormGroup>
                    <Input
                      label="Floating Label"
                      placeholder="Enter text here"
                      floating
                      required
                    />
                  </FormGroup>

                  <FormGroup>
                    <SearchInput
                      placeholder="Search protocols..."
                      onSearch={(value) => handleDemoAction(`Search: ${value}`)}
                    />
                  </FormGroup>

                  <FormGroup>
                    <Input
                      type="password"
                      label="Password Input"
                      placeholder="Enter password"
                    />
                  </FormGroup>

                  <FormGroup>
                    <Input
                      label="Success State"
                      value="Valid input"
                      state="success"
                      successMessage="This input is valid!"
                      readOnly
                    />
                  </FormGroup>

                  <FormGroup>
                    <Input
                      label="Error State"
                      value="Invalid input"
                      state="error"
                      errorMessage="This input has an error!"
                      readOnly
                    />
                  </FormGroup>
                </div>

                <FormGroup>
                  <Textarea
                    label="Textarea"
                    placeholder="Enter a longer description..."
                    helperText="This is a textarea for longer text input"
                  />
                </FormGroup>
              </CardContent>
            </Card>
          </motion.section>

          {/* Loading Components Section */}
          <motion.section variants={itemVariants}>
            <Card className="p-8">
              <CardHeader>
                <CardTitle>Loading Components</CardTitle>
                <CardDescription>
                  Various loading states and progress indicators
                </CardDescription>
              </CardHeader>
              
              <CardContent className="space-y-8">
                {/* Spinners */}
                <div className="space-y-4">
                  <h4 className="text-h4 font-semibold text-rna-charcoal">Spinners</h4>
                  <div className="flex flex-wrap items-center gap-8">
                    <div className="flex flex-col items-center gap-2">
                      <Spinner size="md" />
                      <span className="text-small text-rna-graphite">Standard</span>
                    </div>
                    <div className="flex flex-col items-center gap-2">
                      <RNAHelixSpinner size="md" />
                      <span className="text-small text-rna-graphite">RNA Helix</span>
                    </div>
                    <div className="flex flex-col items-center gap-2">
                      <PulseLoader size="md" />
                      <span className="text-small text-rna-graphite">Pulse</span>
                    </div>
                    <div className="flex flex-col items-center gap-2">
                      <DotsLoader size="md" />
                      <span className="text-small text-rna-graphite">Dots</span>
                    </div>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="space-y-4">
                  <h4 className="text-h4 font-semibold text-rna-charcoal">Progress Bar</h4>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-small text-rna-graphite mb-2">
                        <span>Upload Progress</span>
                        <span>{progress}%</span>
                      </div>
                      <ProgressLoader progress={progress} animated />
                    </div>
                    <Button onClick={handleProgressDemo} size="sm" variant="outline">
                      Animate Progress
                    </Button>
                  </div>
                </div>

                {/* Skeleton Loading */}
                <div className="space-y-4">
                  <h4 className="text-h4 font-semibold text-rna-charcoal">Skeleton Loading</h4>
                  <Card className="p-6">
                    <div className="space-y-4">
                      <Skeleton variant="text" lines={3} />
                      <div className="flex gap-4">
                        <Skeleton variant="circular" width={40} height={40} />
                        <div className="flex-1">
                          <Skeleton variant="text" lines={2} />
                        </div>
                      </div>
                    </div>
                  </Card>
                </div>
              </CardContent>
            </Card>
          </motion.section>
        </motion.div>

        {/* Floating Action Button */}
        <FloatingActionButton
          icon={<BeakerIcon className="w-6 h-6" />}
          onClick={() => handleDemoAction('FAB')}
        />
      </div>
    </div>
  );
};

export default EnhancedComponentsDemo;