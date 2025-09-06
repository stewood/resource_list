"""
AI Utilities Module

This module handles utility functions and helpers for the AI Review Service.
Responsible for data formatting, theme extraction, and enhanced description creation.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from django.db import models

# Set up logging
logger = logging.getLogger(__name__)

# Import the ServiceType model
try:
    from directory.models import ServiceType, TaxonomyCategory
except ImportError:
    # Fallback for when Django is not available (e.g., during testing)
    ServiceType = None
    TaxonomyCategory = None


class AIUtilities:
    """
    Utility functions and helpers for AI verification.
    
    This class handles data formatting, theme extraction, description enhancement,
    and various utility functions for the AI review service.
    """
    
    def __init__(self):
        """Initialize the AI utilities."""
        pass
    
    def _get_service_types_from_db(self) -> List[str]:
        """
        Get service types from the database.
        
        Returns:
            List of service type strings in format "name: description"
        """
        if not ServiceType:
            # Fallback to hardcoded list if Django is not available
            return [
                "Child Care: Child care and family support services",
                "Counseling: Mental health and addiction counseling services",
                "Domestic Violence: Domestic violence prevention and support",
                "Education: Educational programs and support",
                "Emergency Services: Emergency and crisis intervention services",
                "Emergency Shelter: Emergency and temporary housing",
                "Employment: Job training and employment services",
                "Financial Assistance: Financial aid and benefit programs",
                "Food Assistance: Food banks, meal programs, and nutrition assistance",
                "Food Pantry: Food assistance and meal programs",
                "Healthcare: Medical and healthcare services",
                "Hotline: 24/7 crisis and information hotlines",
                "Housing: Housing assistance and shelter services",
                "Job Training: Employment and job training services",
                "Legal Aid: Legal assistance and representation",
                "Legal Services: Legal aid and advocacy services",
                "Medical Care: Healthcare and medical services",
                "Mental Health Counseling: Mental health and counseling services",
                "Pet Care: Pet care and animal services",
                "Substance Abuse: Addiction treatment and recovery services",
                "Substance Abuse Treatment: Addiction recovery and treatment",
                "Transitional Housing: Long-term transitional housing",
                "Transportation: Transportation assistance and services",
                "Utility Assistance: Help with utility bills",
                "Veterans Services: Services specifically for veterans"
            ]
        
        try:
            # Query all service types from the database
            service_types = ServiceType.objects.all().order_by('name')
            return [f"{st.name}: {st.description}" for st in service_types]
        except Exception as e:
            # Fallback to hardcoded list if database query fails
            logger.warning(f"Could not fetch service types from database: {e}")
            return [
                "Child Care: Child care and family support services",
                "Counseling: Mental health and addiction counseling services",
                "Domestic Violence: Domestic violence prevention and support",
                "Education: Educational programs and support",
                "Emergency Services: Emergency and crisis intervention services",
                "Emergency Shelter: Emergency and temporary housing",
                "Employment: Job training and employment services",
                "Financial Assistance: Financial aid and benefit programs",
                "Food Assistance: Food banks, meal programs, and nutrition assistance",
                "Food Pantry: Food assistance and meal programs",
                "Healthcare: Medical and healthcare services",
                "Hotline: 24/7 crisis and information hotlines",
                "Housing: Housing assistance and shelter services",
                "Job Training: Employment and job training services",
                "Legal Aid: Legal assistance and representation",
                "Legal Services: Legal aid and advocacy services",
                "Medical Care: Healthcare and medical services",
                "Mental Health Counseling: Mental health and counseling services",
                "Pet Care: Pet care and animal services",
                "Substance Abuse: Addiction treatment and recovery services",
                "Substance Abuse Treatment: Addiction recovery and treatment",
                "Transitional Housing: Long-term transitional housing",
                "Transportation: Transportation assistance and services",
                "Utility Assistance: Help with utility bills",
                "Veterans Services: Services specifically for veterans"
            ]
    
    def _get_categories_from_db(self) -> List[str]:
        """
        Get categories from the database.
        
        Returns:
            List of category strings in format "name: description"
        """
        if not TaxonomyCategory:
            # Fallback to hardcoded list if Django is not available
            return [
                "Animal Care: Services for Pets and Animals",
                "Child Care: Child care and family services", 
                "Churches: Religious organizations, churches, and faith-based service providers",
                "Community & Social Services: Community centers, social services, and advocacy organizations",
                "Education: Educational programs and services",
                "Emergency Services & Public Safety: Emergency response services, fire departments, law enforcement, and public safety organizations",
                "Food: Food banks and meal programs",
                "Food Assistance: Food banks, pantries, and meal programs",
                "Government & Administrative Services: Government offices, administrative services, and public programs",
                "Healthcare: Medical and mental health services",
                "Hotlines: Emergency and crisis hotlines",
                "Housing: Shelters, housing assistance, and transitional housing",
                "Legal: Legal assistance and advocacy",
                "Medical: Healthcare and medical services",
                "Mental Health: Mental health and substance abuse services",
                "Mental Health & Healthcare Services: Mental health providers, healthcare services, and specialized medical programs",
                "Other: Other services and resources",
                "Shelter: Emergency and transitional housing",
                "Transportation: Transportation assistance",
                "Utilities: Utility assistance programs",
                "Veterans: Veterans services and support"
            ]
        
        try:
            # Query all categories from the database
            categories = TaxonomyCategory.objects.all().order_by('name')
            return [f"{cat.name}: {cat.description}" for cat in categories]
        except Exception as e:
            # Fallback to hardcoded list if database query fails
            logger.warning(f"Could not fetch categories from database: {e}")
            return [
                "Animal Care: Services for Pets and Animals",
                "Child Care: Child care and family services", 
                "Churches: Religious organizations, churches, and faith-based service providers",
                "Community & Social Services: Community centers, social services, and advocacy organizations",
                "Education: Educational programs and services",
                "Emergency Services & Public Safety: Emergency response services, fire departments, law enforcement, and public safety organizations",
                "Food: Food banks and meal programs",
                "Food Assistance: Food banks, pantries, and meal programs",
                "Government & Administrative Services: Government offices, administrative services, and public programs",
                "Healthcare: Medical and mental health services",
                "Hotlines: Emergency and crisis hotlines",
                "Housing: Shelters, housing assistance, and transitional housing",
                "Legal: Legal assistance and advocacy",
                "Medical: Healthcare and medical services",
                "Mental Health: Mental health and substance abuse services",
                "Mental Health & Healthcare Services: Mental health providers, healthcare services, and specialized medical programs",
                "Other: Other services and resources",
                "Shelter: Emergency and transitional housing",
                "Transportation: Transportation assistance",
                "Utilities: Utility assistance programs",
                "Veterans: Veterans services and support"
            ]
    
    def _extract_website_themes(self, content: str) -> List[str]:
        """
        Extract key themes from website content.
        
        Args:
            content: Website content to analyze
            
        Returns:
            List of extracted themes
        """
        try:
            # Simple keyword extraction for key themes
            themes = []
            keywords = ['mission', 'services', 'programs', 'help', 'support', 'community', 
                       'healthcare', 'education', 'housing', 'food', 'assistance', 'outreach']
            
            content_lower = content.lower()
            for keyword in keywords:
                if keyword in content_lower:
                    themes.append(keyword)
            
            return themes[:10]  # Limit to top 10 themes
        except Exception as e:
            return []
    
    def _extract_description_themes(self, description: str) -> List[str]:
        """
        Extract key themes from description.
        
        Args:
            description: Description text to analyze
            
        Returns:
            List of extracted themes
        """
        try:
            # Simple keyword extraction for key themes
            themes = []
            keywords = ['mission', 'services', 'programs', 'help', 'support', 'community', 
                       'healthcare', 'education', 'housing', 'food', 'assistance', 'outreach']
            
            description_lower = description.lower()
            for keyword in keywords:
                if keyword in description_lower:
                    themes.append(keyword)
            
            return themes[:10]  # Limit to top 10 themes
        except Exception as e:
            return []
    
    def _verify_description_tool(self, description: str, website_content: str = None, service_data: dict = None) -> str:
        """
        Verify description quality and accuracy through multiple checks.
        
        Args:
            description: The description text to verify
            website_content: Content from the organization's website
            service_data: Extracted service information
            
        Returns:
            Verification result with findings and suggestions
        """
        try:
            verification_results = []
            
            # 1. Completeness Assessment
            if service_data:
                missing_services = []
                found_services = []
                
                # Check if description mentions key services
                service_fields = ['service_types', 'hours_of_operation', 'eligibility_requirements', 
                                'populations_served', 'cost_information', 'languages_available']
                
                for field in service_fields:
                    if field in service_data and service_data[field]:
                        service_value = service_data[field]
                        if isinstance(service_value, list):
                            for service in service_value:
                                if service.lower() not in description.lower():
                                    missing_services.append(service)
                                else:
                                    found_services.append(service)
                        elif isinstance(service_value, str):
                            if service_value.lower() not in description.lower():
                                missing_services.append(service_value)
                            else:
                                found_services.append(service_value)
                
                if missing_services:
                    verification_results.append(f"Missing services in description: {', '.join(missing_services[:5])}")
                if found_services:
                    verification_results.append(f"Description includes: {', '.join(found_services[:5])}")
            
            # 2. Content Comparison with Website
            if website_content:
                # Extract key themes from website content
                website_themes = self._extract_website_themes(website_content)
                description_themes = self._extract_description_themes(description)
                
                # Check for consistency
                consistent_themes = []
                inconsistent_themes = []
                
                for theme in website_themes:
                    if theme in description_themes:
                        consistent_themes.append(theme)
                    else:
                        inconsistent_themes.append(theme)
                
                if consistent_themes:
                    verification_results.append(f"Consistent with website: {', '.join(consistent_themes[:3])}")
                if inconsistent_themes:
                    verification_results.append(f"Missing from description: {', '.join(inconsistent_themes[:3])}")
            
            # 3. Length and Quality Assessment
            if len(description) < 50:
                verification_results.append("Description is too short - needs more detail")
            elif len(description) > 500:
                verification_results.append("Description is very long - consider condensing")
            
            # 4. Format and Structure Assessment
            if not description.strip():
                verification_results.append("Description is empty")
            elif description.count('.') < 2:
                verification_results.append("Description may need more sentence structure")
            
            return " | ".join(verification_results) if verification_results else "Description verification: No significant issues found"
            
        except Exception as e:
            return f"Description verification error: {str(e)}"
    
    def _verify_service_types_tool(self, current_service_types: list, website_content: str, service_data: dict = None) -> str:
        """
        Verify and suggest the most appropriate service types for a resource.
        
        Args:
            current_service_types: List of current service type names
            website_content: Content from the organization's website
            service_data: Extracted service information
            
        Returns:
            Service type verification result with suggestions
        """
        try:
            # Get available service types from database
            available_service_types = self._get_service_types_from_db()
            
            # Extract key themes and services from website content
            website_themes = self._extract_website_themes(website_content)
            
            # Analyze service data if available
            service_themes = []
            if service_data:
                if service_data.get('service_types'):
                    service_themes.extend(service_data['service_types'])
                if service_data.get('populations_served'):
                    service_themes.append(service_data['populations_served'])
                if service_data.get('eligibility_requirements'):
                    service_themes.append(service_data['eligibility_requirements'])
            
            # Combine all themes for analysis
            all_themes = website_themes + service_themes
            
            # Score each service type based on theme matches
            service_type_scores = {}
            for service_type in available_service_types:
                service_type_name, service_type_desc = service_type.split(": ", 1)
                score = 0
                
                # Score based on service type name matches
                service_type_keywords = service_type_name.lower().split()
                for theme in all_themes:
                    theme_lower = theme.lower()
                    for keyword in service_type_keywords:
                        if keyword in theme_lower:
                            score += 3  # Higher weight for service type matches
                
                # Score based on service type description matches
                desc_keywords = service_type_desc.lower().split()
                for theme in all_themes:
                    theme_lower = theme.lower()
                    for keyword in desc_keywords:
                        if keyword in theme_lower:
                            score += 2
                
                # Special scoring for homeless community context
                homeless_keywords = ['homeless', 'housing', 'shelter', 'transitional', 'emergency', 'crisis', 'poverty']
                community_keywords = ['community', 'social', 'assistance', 'support', 'help', 'outreach']
                
                for theme in all_themes:
                    theme_lower = theme.lower()
                    for keyword in homeless_keywords:
                        if keyword in theme_lower:
                            if any(hk in service_type_name.lower() for hk in ['housing', 'shelter', 'emergency']):
                                score += 4
                            if any(ck in service_type_name.lower() for ck in ['assistance', 'support']):
                                score += 3
                    
                    for keyword in community_keywords:
                        if keyword in theme_lower:
                            if any(ck in service_type_name.lower() for ck in ['assistance', 'support', 'services']):
                                score += 3
                
                service_type_scores[service_type_name] = score
            
            # Find the best matching service types (score > 2)
            recommended_service_types = [(name, score) for name, score in service_type_scores.items() if score > 2]
            recommended_service_types.sort(key=lambda x: x[1], reverse=True)
            
            # Get top 5 service types for comparison
            top_service_types = recommended_service_types[:5]
            
            # Analyze current service types
            current_scores = {}
            for current_type in current_service_types:
                current_scores[current_type] = service_type_scores.get(current_type, 0)
            
            # Generate verification result
            result_parts = []
            
            if current_service_types:
                # Check for service types that should be removed (low scores)
                to_remove = [st for st in current_service_types if service_type_scores.get(st, 0) < 2]
                if to_remove:
                    result_parts.append(f"Service types verification: Consider removing: {', '.join(to_remove)} (low relevance)")
                
                # Check for missing service types (high scores but not in current)
                missing_high_score = [st for st, score in top_service_types if st not in current_service_types and score > 5]
                if missing_high_score:
                    result_parts.append(f"SUGGESTED ADDITIONS: {', '.join(missing_high_score[:3])}")
                
                # Check for service types that are appropriate
                appropriate = [st for st in current_service_types if service_type_scores.get(st, 0) >= 3]
                if appropriate:
                    result_parts.append(f"Appropriate service types: {', '.join(appropriate)}")
                
                if not to_remove and not missing_high_score:
                    result_parts.append(f"Service types verification: Current service types are appropriate")
            else:
                result_parts.append(f"Service types verification: No current service types specified")
                if top_service_types:
                    result_parts.append(f"RECOMMENDED SERVICE TYPES: {', '.join([st[0] for st in top_service_types[:3]])}")
            
            # Add reasoning
            result_parts.append(f"REASONING: Based on website themes: {', '.join(website_themes[:5])}")
            if service_themes:
                result_parts.append(f"Service themes: {', '.join(service_themes[:3])}")
            
            # Add top service types for comparison
            if top_service_types:
                result_parts.append(f"TOP SERVICE TYPES: {', '.join([f'{st[0]} ({st[1]})' for st in top_service_types])}")
            
            # Check if we need new service types
            if not recommended_service_types:
                result_parts.append(f"SUGGEST NEW SERVICE TYPE: Consider creating a new service type for this specialized service")
                result_parts.append(f"CONTEXT: London, KY homeless community resource directory")
            
            return " | ".join(result_parts)
            
        except Exception as e:
            return f"Service types verification error: {str(e)}"
    
    def _verify_category_tool(self, current_category: str, website_content: str, service_data: dict = None) -> str:
        """
        Verify and suggest the most appropriate category for a resource.
        
        Args:
            current_category: The current category name
            website_content: Content from the organization's website
            service_data: Extracted service information
            
        Returns:
            Category verification result with suggestions
        """
        try:
            # Get available categories from database
            available_categories = self._get_categories_from_db()
            
            # Extract key themes and services from website content
            website_themes = self._extract_website_themes(website_content)
            
            # Analyze service data if available
            service_themes = []
            if service_data:
                if service_data.get('service_types'):
                    service_themes.extend(service_data['service_types'])
                if service_data.get('populations_served'):
                    service_themes.append(service_data['populations_served'])
                if service_data.get('eligibility_requirements'):
                    service_themes.append(service_data['eligibility_requirements'])
            
            # Combine all themes for analysis
            all_themes = website_themes + service_themes
            
            # Score each category based on theme matches
            category_scores = {}
            for category in available_categories:
                category_name, category_desc = category.split(": ", 1)
                score = 0
                
                # Score based on category name matches
                category_keywords = category_name.lower().split()
                for theme in all_themes:
                    theme_lower = theme.lower()
                    for keyword in category_keywords:
                        if keyword in theme_lower:
                            score += 2
                
                # Score based on category description matches
                desc_keywords = category_desc.lower().split()
                for theme in all_themes:
                    theme_lower = theme.lower()
                    for keyword in desc_keywords:
                        if keyword in theme_lower:
                            score += 1
                
                # Special scoring for homeless community context
                homeless_keywords = ['homeless', 'housing', 'shelter', 'transitional', 'emergency', 'crisis']
                community_keywords = ['community', 'social', 'assistance', 'support', 'help']
                
                for theme in all_themes:
                    theme_lower = theme.lower()
                    for keyword in homeless_keywords:
                        if keyword in theme_lower:
                            if 'housing' in category_name.lower() or 'shelter' in category_name.lower():
                                score += 3
                            if 'community' in category_name.lower() or 'social' in category_name.lower():
                                score += 2
                    
                    for keyword in community_keywords:
                        if keyword in theme_lower:
                            if 'community' in category_name.lower() or 'social' in category_name.lower():
                                score += 2
                
                category_scores[category_name] = score
            
            # Find the best matching category
            best_category = max(category_scores.items(), key=lambda x: x[1])
            best_score = best_category[1]
            best_category_name = best_category[0]
            
            # Get top 3 categories for comparison
            top_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Analyze current category
            current_score = category_scores.get(current_category, 0) if current_category else 0
            
            # Generate verification result
            result_parts = []
            
            if current_category:
                if current_category == best_category_name:
                    result_parts.append(f"Category verification: Current category '{current_category}' is appropriate (score: {current_score})")
                elif best_score > current_score + 2:  # Significant improvement
                    result_parts.append(f"Category verification: Current category '{current_category}' (score: {current_score}) may not be optimal")
                    result_parts.append(f"SUGGESTED CATEGORY: '{best_category_name}' (score: {best_score})")
                else:
                    result_parts.append(f"Category verification: Current category '{current_category}' is acceptable (score: {current_score})")
            else:
                result_parts.append(f"Category verification: No current category specified")
                result_parts.append(f"RECOMMENDED CATEGORY: '{best_category_name}' (score: {best_score})")
            
            # Add reasoning
            result_parts.append(f"REASONING: Based on website themes: {', '.join(website_themes[:5])}")
            if service_themes:
                result_parts.append(f"Service themes: {', '.join(service_themes[:3])}")
            
            # Add top categories for comparison
            result_parts.append(f"TOP CATEGORIES: {', '.join([f'{cat[0]} ({cat[1]})' for cat in top_categories])}")
            
            # Check if we need a new category
            if best_score < 3:  # Low confidence in existing categories
                result_parts.append(f"SUGGEST NEW CATEGORY: Consider creating a new category for this specialized service")
                result_parts.append(f"CONTEXT: London, KY homeless community resource directory")
            
            return " | ".join(result_parts)
            
        except Exception as e:
            return f"Category verification error: {str(e)}"
    
    def _create_enhanced_description(self, current_description: str, service_data: dict, website_content: str = None) -> str:
        """
        Create an enhanced description by adding missing information.
        
        Args:
            current_description: The current description text
            service_data: Extracted service information
            website_content: Website content for additional context
            
        Returns:
            Enhanced description with missing information added
        """
        try:
            enhanced_parts = [current_description]
            
            # Add missing service details
            if service_data:
                additional_details = []
                
                # Add hours if not mentioned
                if 'hours_of_operation' in service_data and service_data['hours_of_operation']:
                    if service_data['hours_of_operation'].lower() not in current_description.lower():
                        additional_details.append(f"Operating hours: {service_data['hours_of_operation']}")
                
                # Add eligibility if not mentioned
                if 'eligibility_requirements' in service_data and service_data['eligibility_requirements']:
                    if service_data['eligibility_requirements'].lower() not in current_description.lower():
                        additional_details.append(f"Eligibility: {service_data['eligibility_requirements']}")
                
                # Add populations if not mentioned
                if 'populations_served' in service_data and service_data['populations_served']:
                    if service_data['populations_served'].lower() not in current_description.lower():
                        additional_details.append(f"Populations served: {service_data['populations_served']}")
                
                # Add cost information if not mentioned
                if 'cost_information' in service_data and service_data['cost_information']:
                    if service_data['cost_information'].lower() not in current_description.lower():
                        additional_details.append(f"Cost information: {service_data['cost_information']}")
                
                # Add languages if not mentioned
                if 'languages_available' in service_data and service_data['languages_available']:
                    if service_data['languages_available'].lower() not in current_description.lower():
                        additional_details.append(f"Languages: {service_data['languages_available']}")
                
                if additional_details:
                    enhanced_parts.append(" " + ". ".join(additional_details) + ".")
            
            # Add website themes if missing
            if website_content:
                website_themes = self._extract_website_themes(website_content)
                description_themes = self._extract_description_themes(current_description)
                
                missing_themes = [theme for theme in website_themes if theme not in description_themes]
                if missing_themes:
                    theme_text = ", ".join(missing_themes[:3])
                    enhanced_parts.append(f" The organization focuses on {theme_text} initiatives.")
            
            return " ".join(enhanced_parts)
            
        except Exception as e:
            return current_description
    
    def _format_data_for_display(self, data: Dict[str, Any]) -> str:
        """
        Format data for display in reports or UI.
        
        Args:
            data: Data dictionary to format
            
        Returns:
            Formatted string representation
        """
        try:
            formatted_lines = []
            for key, value in data.items():
                if value:
                    if isinstance(value, list):
                        formatted_lines.append(f"{key}: {', '.join(value)}")
                    else:
                        formatted_lines.append(f"{key}: {value}")
            return "\n".join(formatted_lines)
        except Exception as e:
            return f"Error formatting data: {str(e)}"
    
    def _clean_text_content(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned and normalized text
        """
        try:
            if not text:
                return text
            
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Remove special characters that might cause issues
            text = re.sub(r'[^\w\s\.\,\-\:\;\!\?\(\)]', '', text)
            
            # Normalize line breaks
            text = text.replace('\n', ' ').replace('\r', ' ')
            
            return text.strip()
        except Exception as e:
            return text
