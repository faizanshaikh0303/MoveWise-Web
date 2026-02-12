import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const LandingPage = () => {
  const navigate = useNavigate();
  const [scrollY, setScrollY] = useState(0);
  const [mousePosition, setMousePosition] = useState({ x: 0.5, y: 0.5 });

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: e.clientX / window.innerWidth,
        y: e.clientY / window.innerHeight,
      });
    };

    window.addEventListener('scroll', handleScroll);
    window.addEventListener('mousemove', handleMouseMove);
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  // Intersection Observer for scroll animations
  useEffect(() => {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-in');
        }
      });
    }, observerOptions);

    document.querySelectorAll('.scroll-animate').forEach(el => {
      observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  const features = [
    {
      title: 'Cost of Living',
      description: 'Compare housing, groceries, utilities, and more. Know exactly how much you\'ll spend in your new city.',
      image: '/features/cost-living.jpg',
      gradient: 'from-green-400/20 to-emerald-600/20',
    },
    {
      title: 'Safety Analysis',
      description: 'Real crime data from FBI statistics. Understand the safety profile of your potential neighborhood.',
      image: '/features/safety.jpg',
      gradient: 'from-blue-400/20 to-blue-600/20',
    },
    {
      title: 'Local Amenities',
      description: 'Find gyms, restaurants, parks, and entertainment near you. Match your lifestyle preferences.',
      image: '/features/amenities.jpg',
      gradient: 'from-purple-400/20 to-pink-600/20',
    },
    {
      title: 'Commute Time',
      description: 'Calculate your daily commute by car, transit, bike, or walking. Optimize your time.',
      image: '/features/commute.jpg',
      gradient: 'from-yellow-400/20 to-orange-600/20',
    },
    {
      title: 'Noise Levels',
      description: 'Understand the sound environment. Find quiet suburbs or vibrant city centers based on your preference.',
      image: '/features/noise.jpg',
      gradient: 'from-indigo-400/20 to-purple-600/20',
    },
    {
      title: 'AI Insights',
      description: 'Get personalized recommendations based on your lifestyle, work schedule, and preferences.',
      image: '/features/ai-insights.jpg',
      gradient: 'from-pink-400/20 to-red-600/20',
    },
  ];

  const steps = [
    {
      step: '01',
      title: 'Set Up Your Profile',
      description: 'Tell us about your work schedule, sleep patterns, and lifestyle preferences. This helps us personalize your analysis.',
      image: '/steps/step-1.jpg',
      direction: 'left',
    },
    {
      step: '02',
      title: 'Enter Your Locations',
      description: 'Input your current address and where you\'re considering moving. We\'ll gather data from multiple sources.',
      image: '/steps/step-2.jpg',
      direction: 'right',
    },
    {
      step: '03',
      title: 'Get AI-Powered Insights',
      description: 'Receive a comprehensive report with data visualizations, comparisons, and personalized recommendations.',
      image: '/steps/step-3.jpg',
      direction: 'left',
    },
  ];

  return (
    <div className="bg-white">
      {/* Fixed Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-lg border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/')}>
              <div className="bg-white rounded-xl p-1.5 shadow-sm">
                <img 
                  src="/logo.png" 
                  alt="MoveWise Logo" 
                  className="w-8 h-8 object-contain"
                  onError={(e) => {
                    // Fallback to gradient if image doesn't load
                    e.currentTarget.style.display = 'none';
                    e.currentTarget.parentElement?.classList.add('bg-gradient-to-br', 'from-primary', 'to-blue-600');
                    const fallback = e.currentTarget.parentElement?.nextElementSibling as HTMLElement;
                    if (fallback) {
                      fallback.classList.remove('hidden');
                      fallback.style.display = 'flex';
                    }
                  }}
                />
              </div>
              <div className="hidden w-10 h-10 bg-gradient-to-br from-primary to-blue-600 rounded-xl items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
                MoveWise
              </span>
            </div>

            {/* Sign In Button */}
            <button
              onClick={() => navigate('/login')}
              className="px-6 py-2.5 bg-gradient-to-r from-primary to-blue-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200"
            >
              Sign In
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Cursor-Following Animated Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div 
              className="absolute w-96 h-96 bg-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-30 transition-all duration-1000 ease-out"
              style={{
                top: `${-10 + mousePosition.y * 20}%`,
                right: `${-10 + mousePosition.x * 20}%`,
              }}
            ></div>
            <div 
              className="absolute w-96 h-96 bg-blue-300 rounded-full mix-blend-multiply filter blur-xl opacity-30 transition-all duration-1000 ease-out"
              style={{
                bottom: `${-10 + (1 - mousePosition.y) * 20}%`,
                left: `${-10 + (1 - mousePosition.x) * 20}%`,
              }}
            ></div>
            <div 
              className="absolute w-96 h-96 bg-pink-300 rounded-full mix-blend-multiply filter blur-xl opacity-30 transition-all duration-1000 ease-out"
              style={{
                top: `${40 + mousePosition.y * 10}%`,
                left: `${40 + mousePosition.x * 10}%`,
              }}
            ></div>
          </div>
        </div>

        {/* Hero Content */}
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center z-10 pt-20">
          <div 
            className="animate-fade-in-up"
            style={{
              transform: `translateY(${scrollY * 0.2}px)`,
              opacity: Math.max(0, 1 - scrollY / 500),
            }}
          >
            <h1 className="text-6xl md:text-7xl lg:text-8xl font-bold mb-6">
              <span className="bg-gradient-to-r from-primary via-blue-600 to-purple-600 bg-clip-text text-transparent">
                Make Smarter
              </span>
              <br />
              <span className="text-gray-900">Moving Decisions</span>
            </h1>
            
            <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-3xl mx-auto">
              AI-powered location analysis to help you find the perfect neighborhood.
              Compare cities, costs, safety, and lifestyle in seconds.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => navigate('/login')}
                className="px-8 py-4 bg-gradient-to-r from-primary to-blue-600 text-white rounded-xl font-semibold text-lg shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all duration-200"
              >
                Start Your Analysis
              </button>
              <button
                onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
                className="px-8 py-4 bg-white text-gray-900 rounded-xl font-semibold text-lg shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 border-2 border-gray-200"
              >
                See How It Works
              </button>
            </div>

            {/* Scroll Indicator */}
            <div className="mt-16 animate-bounce">
              <svg className="w-6 h-6 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
              </svg>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Everything You Need to Know
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Comprehensive insights powered by AI to make your relocation decision easier
            </p>
          </div>

          {/* Feature Grid with Image Backgrounds */}
          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, idx) => (
              <div
                key={idx}
                className="group relative rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:scale-105 h-64"
              >
                {/* Background Image */}
                <div 
                  className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-110"
                  style={{
                    backgroundImage: `url(${feature.image})`,
                  }}
                >
                  {/* Fallback gradient if image doesn't load */}
                  <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient}`}></div>
                  {/* Dark overlay for text readability */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/30 to-transparent"></div>
                </div>

                {/* Content */}
                <div className="relative h-full p-8 flex flex-col justify-end text-white z-10">
                  <h3 className="text-2xl font-bold mb-3 drop-shadow-lg">{feature.title}</h3>
                  <p className="text-white/90 leading-relaxed drop-shadow-md">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 bg-gradient-to-br from-gray-50 to-blue-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Get your personalized analysis in three simple steps
            </p>
          </div>

          {/* Steps with Directional Animations */}
          <div className="space-y-24">
            {steps.map((step, idx) => (
              <div
                key={idx}
                className={`scroll-animate flex flex-col ${
                  step.direction === 'left' ? 'md:flex-row' : 'md:flex-row-reverse'
                } items-center gap-12 opacity-0`}
                style={{
                  transform: step.direction === 'left' ? 'translateX(-100px)' : 'translateX(100px)',
                }}
              >
                {/* Text Content */}
                <div className="flex-1">
                  <div className="text-6xl md:text-8xl font-bold text-pink-400 mb-4">{step.step}</div>
                  <h3 className="text-3xl md:text-4xl font-bold text-blue-500 mb-4">{step.title}</h3>
                  <p className="text-xl text-gray-600 leading-relaxed">{step.description}</p>
                </div>

                {/* Image */}
                <div className="flex-1 flex items-center justify-center">
                  <div className="relative w-full max-w-md aspect-square">
                    <img 
                      src={step.image} 
                      alt={step.title}
                      className="w-full h-full object-cover rounded-2xl shadow-2xl"
                      onError={(e) => {
                        // Fallback gradient background
                        e.currentTarget.style.display = 'none';
                        const fallback = e.currentTarget.nextElementSibling;
                        if (fallback) {
                          (fallback as HTMLElement).style.display = 'flex';
                        }
                      }}
                    />
                    {/* Fallback */}
                    <div className="hidden w-full h-full bg-gradient-to-br from-primary to-purple-600 rounded-2xl items-center justify-center text-white text-6xl">
                      {idx === 0 ? '🏠' : idx === 1 ? '📍' : '🤖'}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 bg-blue-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-3 gap-8 text-center">
            {[
              { number: '70+', label: 'Cities Covered' },
              { number: '5', label: 'Data Sources' },
              { number: '100%', label: 'Personalized' },
            ].map((stat, idx) => (
              <div key={idx} className="animate-fade-in-up" style={{ animationDelay: `${idx * 0.1}s` }}>
                <div className="text-5xl md:text-6xl font-bold mb-2 bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">{stat.number}</div>
                <div className="text-xl text-gray-700">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="bg-gradient-to-r from-primary via-blue-600 to-purple-600 text-4xl md:text-5xl font-bold mb-6 bg-clip-text text-transparent">
            Ready to Find Your Perfect Place?
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Join thousands making smarter moving decisions with AI-powered insights
          </p>
          <button
            onClick={() => navigate('/login')}
            className="px-10 py-5 bg-gradient-to-r from-primary to-blue-600 text-white rounded-xl font-semibold text-xl shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all duration-200"
          >
            Get Started for Free
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-purple-100 text-gray-800 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center gap-2 mb-4 md:mb-0 cursor-pointer" onClick={() => navigate('/')}>
              <div className="bg-purple-100 rounded-xl p-1.5 shadow-sm">
                <img 
                  src="/logo.png" 
                  alt="MoveWise Logo" 
                  className="w-8 h-8 object-contain"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                    e.currentTarget.parentElement?.classList.add('bg-gradient-to-br', 'from-primary', 'to-blue-600');
                    const fallback = e.currentTarget.parentElement?.nextElementSibling as HTMLElement;
                    if (fallback) {
                      fallback.classList.remove('hidden');
                      fallback.style.display = 'flex';
                    }
                  }}
                />
              </div>
              <div className="hidden w-10 h-10 bg-gradient-to-br from-primary to-blue-600 rounded-xl items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <span className="text-xl font-bold">MoveWise</span>
            </div>
            <div className="text-gray-600 text-sm">
              © 2026 MoveWise. Making relocation decisions smarter.
            </div>
          </div>
        </div>
      </footer>

      {/* Animations & Styles */}
      <style>{`
        @keyframes fade-in-up {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-fade-in-up {
          animation: fade-in-up 0.8s ease-out both;
        }

        .scroll-animate {
          transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .scroll-animate.animate-in {
          opacity: 1 !important;
          transform: translateX(0) !important;
        }
      `}</style>
    </div>
  );
};

export default LandingPage;
