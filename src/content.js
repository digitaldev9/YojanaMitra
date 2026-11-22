import { BadgeIndianRupee, Bot, Bookmark, ClipboardCheck, FileText, GraduationCap, Heart, Languages, Mic, Rocket, Sprout, createLucideIcon } from 'lucide-react'

const Venus = createLucideIcon('Venus', [
  ['circle', { cx: 12, cy: 8, r: 6, key: 'ring' }],
  ['path', { d: 'M12 14v8m-4-4h8', key: 'stem' }],
])

export const categories = [
  { name: 'Students', theme: 'student', icon: GraduationCap, query: 'student scholarships education loans skill development', description: 'Scholarships, education loans, skill development and more.' },
  { name: 'Women', theme: 'women', icon: Venus, query: 'women financial assistance maternity entrepreneurship schemes', description: 'Financial assistance, maternity benefits, entrepreneurship and empowerment schemes.' },
  { name: 'Farmers', theme: 'farmer', icon: Sprout, query: 'farmer agricultural subsidies crop insurance irrigation schemes', description: 'Agricultural subsidies, crop insurance, irrigation support and more.' },
]

export const suggestions = [
  ['Scholarship', GraduationCap, 'student'], ['Women Empowerment', Venus, 'women'],
  ['Farmer Subsidy', Sprout, 'farmer'], ['Startup Support', Rocket, 'saffron'], ['Maternity Benefit', Heart, 'women'],
]

export const features = [
  ['AI Scheme Search', 'Powered by You.com', Bot, 'student', 'search'],
  ['Check Your Eligibility', '', ClipboardCheck, 'farmer', 'eligibility'],
  ['Fill & Prepare Application Form', '', FileText, 'violet', 'application'],
  ['Multi-language', 'English | Hindi | Marathi', Languages, 'farmer', 'language'],
  ['Voice Search', 'Speak & Search', Mic, 'women', 'voice'],
  ['Save & Track Schemes', '', Bookmark, 'saffron', 'saved'],
]

export const languages = { en: ['English', 'en-IN'], hi: ['हिन्दी', 'hi-IN'], mr: ['मराठी', 'mr-IN'] }
export const schemeIcons = [GraduationCap, Venus, Sprout, BadgeIndianRupee]

const labels = [
  'Home', 'Schemes', 'Eligibility Checker', 'Application Assistant', 'About', 'Login / Sign Up',
  'Your Guide to Government Schemes', 'Government Scheme Discovery Platform',
  'Discover Government Schemes', 'Made for You',
  'Find, understand, and apply for government schemes easily with AI.',
  'Search any scheme... e.g. scholarship for students, loan for women, farm subsidy',
  'Search', 'Popular Searches', 'Students', 'Women', 'Farmers', 'Explore Schemes',
  'Featured Government Schemes', 'View All Schemes', 'Explore some important and widely available government schemes.',
  'View Details', 'How can I help you today?', 'Ask anything about schemes...', 'Your AI Government Scheme Assistant',
  'Scholarship', 'Women Empowerment', 'Farmer Subsidy', 'Startup Support', 'Maternity Benefit',
  'Scholarships, education loans, skill development and more.',
  'Financial assistance, maternity benefits, entrepreneurship and empowerment schemes.',
  'Agricultural subsidies, crop insurance, irrigation support and more.',
  'AI Scheme Search', 'Powered by You.com', 'Check Your Eligibility', 'Fill & Prepare Application Form',
  'Multi-language', 'English | Hindi | Marathi', 'Voice Search', 'Speak & Search', 'Save & Track Schemes',
  'Find schemes for me', 'Check my eligibility', 'How to apply?', 'Required documents',
]
const hi = [
  'होम', 'योजनाएँ', 'पात्रता जाँच', 'आवेदन सहायक', 'परिचय', 'लॉग इन / साइन अप',
  'सरकारी योजनाओं के लिए आपका मार्गदर्शक', 'सरकारी योजना खोज मंच', 'सरकारी योजनाएँ खोजें', 'आपके लिए',
  'एआई की मदद से सरकारी योजनाएँ खोजें, समझें और आवेदन करें।',
  'कोई योजना खोजें... छात्रवृत्ति, महिला ऋण, कृषि सब्सिडी', 'खोजें', 'लोकप्रिय खोजें', 'विद्यार्थी', 'महिलाएँ', 'किसान',
  'योजनाएँ देखें', 'प्रमुख सरकारी योजनाएँ', 'सभी योजनाएँ देखें', 'कुछ महत्वपूर्ण और व्यापक रूप से उपलब्ध सरकारी योजनाएँ देखें।',
  'विवरण देखें', 'आज मैं आपकी कैसे मदद कर सकता हूँ?', 'योजनाओं के बारे में पूछें...', 'आपका एआई सरकारी योजना सहायक',
  'छात्रवृत्ति', 'महिला सशक्तिकरण', 'कृषि सब्सिडी', 'स्टार्टअप सहायता', 'मातृत्व लाभ',
  'छात्रवृत्ति, शिक्षा ऋण, कौशल विकास और बहुत कुछ।',
  'वित्तीय सहायता, मातृत्व लाभ, उद्यमिता और सशक्तिकरण योजनाएँ।',
  'कृषि सब्सिडी, फसल बीमा, सिंचाई सहायता और बहुत कुछ।',
  'एआई योजना खोज', 'You.com द्वारा संचालित', 'अपनी पात्रता जाँचें', 'आवेदन पत्र तैयार करें',
  'बहुभाषी', 'अंग्रेज़ी | हिन्दी | मराठी', 'आवाज़ से खोजें', 'बोलें और खोजें', 'योजनाएँ सहेजें और ट्रैक करें',
  'मेरे लिए योजनाएँ खोजें', 'मेरी पात्रता जाँचें', 'आवेदन कैसे करें?', 'आवश्यक दस्तावेज़',
]
const mr = [
  'मुख्यपृष्ठ', 'योजना', 'पात्रता तपासणी', 'अर्ज सहाय्यक', 'माहिती', 'लॉग इन / साइन अप',
  'शासकीय योजनांसाठी तुमचा मार्गदर्शक', 'शासकीय योजना शोध व्यासपीठ', 'शासकीय योजना शोधा', 'तुमच्यासाठी',
  'एआयच्या मदतीने शासकीय योजना शोधा, समजून घ्या आणि अर्ज करा.',
  'योजना शोधा... शिष्यवृत्ती, महिला कर्ज, शेती अनुदान', 'शोधा', 'लोकप्रिय शोध', 'विद्यार्थी', 'महिला', 'शेतकरी',
  'योजना पाहा', 'निवडक शासकीय योजना', 'सर्व योजना पाहा', 'महत्त्वाच्या आणि व्यापकपणे उपलब्ध शासकीय योजना पाहा.',
  'तपशील पाहा', 'आज मी तुम्हाला कशी मदत करू?', 'योजनांबद्दल विचारा...', 'तुमचा एआय शासकीय योजना सहाय्यक',
  'शिष्यवृत्ती', 'महिला सक्षमीकरण', 'शेती अनुदान', 'स्टार्टअप सहाय्य', 'मातृत्व लाभ',
  'शिष्यवृत्ती, शैक्षणिक कर्ज, कौशल्य विकास आणि बरेच काही.',
  'आर्थिक सहाय्य, मातृत्व लाभ, उद्योजकता आणि सक्षमीकरण योजना.',
  'कृषी अनुदान, पीक विमा, सिंचन सहाय्य आणि बरेच काही.',
  'एआय योजना शोध', 'You.com द्वारे संचालित', 'तुमची पात्रता तपासा', 'अर्ज भरा आणि तयार करा',
  'बहुभाषिक', 'इंग्रजी | हिन्दी | मराठी', 'आवाजाने शोधा', 'बोला आणि शोधा', 'योजना जतन करा आणि मागोवा घ्या',
  'माझ्यासाठी योजना शोधा', 'माझी पात्रता तपासा', 'अर्ज कसा करावा?', 'आवश्यक कागदपत्रे',
]
const translations = { hi, mr }
const pageLabels = {
  'Scheme Search': ['योजना खोज', 'योजना शोध'],
  'Scheme details': ['योजना विवरण', 'योजनेचा तपशील'],
  'State or union territory': ['राज्य या केंद्र शासित प्रदेश', 'राज्य किंवा केंद्रशासित प्रदेश'],
  'Occupation': ['व्यवसाय', 'व्यवसाय'],
  'Education level': ['शिक्षा का स्तर', 'शिक्षणाची पातळी'],
  'Category': ['वर्ग', 'प्रवर्ग'],
  'Gender (optional)': ['लिंग (वैकल्पिक)', 'लिंग (ऐच्छिक)'],
  'Interest': ['रुचि', 'स्वारस्य'],
  'Age': ['आयु', 'वय'],
  'Annual family income (₹, optional)': ['वार्षिक पारिवारिक आय (₹, वैकल्पिक)', 'वार्षिक कौटुंबिक उत्पन्न (₹, ऐच्छिक)'],
  'Find matching schemes': ['उपयुक्त योजनाएँ खोजें', 'जुळणाऱ्या योजना शोधा'],
  'Saved schemes': ['सहेजी गई योजनाएँ', 'जतन केलेल्या योजना'],
  'About YojanaSetu': ['योजनासेतु के बारे में', 'योजनासेतूविषयी'],
}
export const translate = (language, label) =>
  translations[language]?.[labels.indexOf(label)] || pageLabels[label]?.[['hi', 'mr'].indexOf(language)] || label
