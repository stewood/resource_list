#!/usr/bin/env python
"""
Script to update existing resources with enhanced information from London KY research report.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
django.setup()

from directory.models import Resource

def update_existing_resources():
    """Update existing resources with enhanced information from the research report."""
    
    # Dictionary of resource names and their enhanced descriptions
    enhanced_descriptions = {
        "First Presbyterian Church": "Provides community food pantry for residents of Laurel County. Food pantry operates on Thursdays from 11:00 am to 2:00 pm. Must be a resident of Laurel County.",
        
        "First United Methodist Church": "Operates emergency food pantry for those in need in Laurel County. Food pantry open Monday through Thursday, from 10:00 am to 2:00 pm. Serves residents of London and Laurel County.",
        
        "Good Samaritan House Homeless Shelter": "Provides shelter for up to 30 individuals. Also functions as emergency warming center during periods of extreme cold weather. Operational partnership with Isaiah 58:10 Ministries, which runs soup kitchen out of same facility, creating centralized hub for both shelter and meals. Shelter open 24/7 for residents. Soup kitchen operates Monday, Tuesday, Thursday, and Saturday from 11 a.m. to 1 p.m. Specific and stringent intake requirements - must be Kentucky resident, pass warrant check, 10-panel drug test, and background check. Clients must be willing and able to work, required to secure employment within seven days of entry or have existing source of income. Serves 'working homeless' population ready to engage in structured programming.",
        
        "Housing Authority of London": "Manages public housing options within city of London. Separate from Laurel County Housing Authority, which administers Section 8 voucher program for broader county area. Clients seeking housing assistance must apply to each authority separately.",
        
        "Laurel County Housing Authority": "Administers Housing Choice Voucher Program (Section 8) for Laurel County. Provides rental assistance vouchers to low-income families, elderly, and those with disabilities, allowing them to lease privately owned housing. Distinct from Housing Authority of London, which manages public housing units. Hours Monday-Friday, 8:00 am to 4:00 pm (closed for lunch 12:00 pm-1:00 pm). Must be resident of Laurel County and meet federal income guidelines. Required documents include Social Security cards, birth certificates, and income information for all household members.",
        
        "London Police Department": "Municipal law enforcement for City of London. For emergencies, dial 911.",
        
        "London Women's Care": "Provides OB/GYN and other specialized medical services for women.",
        
        "New Harvest Church": "Offers community food pantry for eligible Laurel County residents. Pantry hours irregular; calling ahead required to confirm details. Must be resident of Laurel County and meet income guidelines. Picture ID, proof of income, and proof of residency required.",
        
        "New Salem Baptist Church": "Provides food pantry for Laurel County residents. Emergency food baskets may also be available. Hours vary by source - Thursdays from 9:30 am to 11:00 am or Thursdays from 11:00 am to 1:00 pm and last Tuesday of month from 6:00 pm to 7:00 pm. Calling ahead highly recommended to confirm current schedule. Serves residents of Laurel County.",
        
        "Operation UNITE": "Comprehensive, multi-faceted anti-drug initiative serving 32 counties in Southeastern Kentucky. Three-pronged approach includes: Education - Youth camps, school-based prevention programs, and scholarships for high school seniors. Treatment - Provides treatment referral helpline (KY HELP) and offers one-time treatment vouchers for low-income residents to obtain long-term residential treatment. Enforcement - Operates anonymous drug tip line and collaborates with law enforcement on narcotics investigations. Main office hours Monday-Friday, 8:00 am to 5:00 pm. Hotlines operate 24/7. KY HELP Hotline: (833) 859-4357. Drug Tip Line: (866) 424-4382.",
        
        "Recovery Ridge": "Provides safe, affordable, and structured sober living residences for men recovering from alcohol and drug addiction. Program based on 12-step structure and provides supportive services to help individuals avoid relapse. Allows for Medication-Assisted Treatment (MAT) with certain requirements. Recovery services include case management, therapy (individual and group), and anger management. Serves adult men, including veterans. Recommended stay 6 months. Self-pay accepted, with payment plan available. Operates multiple sober living homes for men in and around London, including locations at 187 Parker Road, 2111 North Laurel Rd, and 279 Campground School Rd.",
        
        "Second Mile Behavioral Health": "Mental health collective providing therapy, case management, and community support services for individuals in Laurel and surrounding counties. Addresses substance abuse, behavioral health, mental health, and family issues, and accepts court referrals. Hours 9:00 am - 6:00 pm. Also operates second London office at 94 Dog Patch Trading Center.",
        
        "Stepworks Recovery Centers of London": "CARF-accredited 30-day residential substance abuse treatment facility. London location serves men exclusively. Services include medical detoxification, individual, group, and family therapy, life skills training, and case management to support long-term sobriety. Offers whole-person approach to treatment and provides intensive outpatient therapies to aid transition back into community. Facility operates 24/7. Serves men aged 18 and older. Accepts Medicaid, private insurance, and private pay.",
        
        "Structure House Recovery": "501(c)(3) non-profit organization providing substance abuse program for prevention and treatment of dependency. Operates as sober living facility. Relatively new organization, formed in 2021. Distinct from other recovery homes in area.",
        
        "Baptist Health Corbin": "Major regional hospital providing full range of medical services. Includes Baptist Health Trillium Center, which offers detoxification services for substance use disorders, making it key medical entry point for individuals beginning recovery. Also primary provider of prenatal care in area.",
        
        "White Flag Ministry": "Unique, seasonal, and weather-dependent model. Not traditional shelter building but program providing emergency overnight shelter and food during winter months (typically Monday after Thanksgiving through mid-March). When temperature forecast to drop below threshold, ministry activates 'shelter nights.' Individuals must check in at Burkhart Center between 4:00 PM and 5:00 PM to be registered and receive voucher for room at local hotel on first-come, first-served basis. Regardless of shelter status, provides hot meal, warm clothing, blankets, and access to counseling resources at Burkhart Center every weekday from 4:00 PM to 5:00 PM during operational season. Leverages partnerships with host church (St. John's), counseling agency for case management (RRJ Solutions), and local hotels for lodging.",
        
        "Winds of Change Counseling Services": "Provides range of tailored mental health and substance use counseling services. Organization aims to create safe place for healing and offers professional support across spectrum of needs. Also operates office at 105 S Pine St, Pineville, KY 40977.",
        
        "KCEOC Community Action Partnership": "Major community action agency serving 16 counties in eastern and central Kentucky with wide array of programs designed to promote self-sufficiency. Key programs relevant to homelessness include: Emergency Support Center - Provides temporary emergency shelter for women and children who meet McKinney-Vento homeless assistance guidelines. Housing Programs - Manages apartment rentals, offers homeowner rehabilitation program, provides housing counseling, and administers Tenant Based Rental Assistance for security and utility deposits. Youth Homelessness - Operates Ryan's Place, crisis center and shelter for homeless youth aged 18-24. Energy and Food - Administers LIHEAP (energy assistance), Project Winter Care, and Summer Food Service Program for children. Employment - Kentucky Career Center Jobsight program provides career guidance, job placement, and skills training.",
        
        "National Domestic Violence Hotline": "Provides 24/7, free, confidential support to anyone affected by domestic violence. Advocates available to offer crisis intervention, safety planning, and referrals to local resources, which can include emergency shelters like Cumberland Valley Domestic Violence Services."
    }
    
    updated_count = 0
    not_found_count = 0
    
    for resource_name, enhanced_description in enhanced_descriptions.items():
        try:
            resource = Resource.objects.get(name=resource_name)
            
            # Check if the description needs updating
            if resource.description != enhanced_description:
                print(f"Updating: {resource_name}")
                print(f"  Old: {resource.description[:100]}...")
                print(f"  New: {enhanced_description[:100]}...")
                
                resource.description = enhanced_description
                resource.save()
                updated_count += 1
            else:
                print(f"Already up to date: {resource_name}")
                
        except Resource.DoesNotExist:
            print(f"Resource not found: {resource_name}")
            not_found_count += 1
    
    print(f"\nUpdate Summary:")
    print(f"  Updated: {updated_count}")
    print(f"  Not found: {not_found_count}")
    print(f"  Total processed: {len(enhanced_descriptions)}")

if __name__ == "__main__":
    update_existing_resources()
