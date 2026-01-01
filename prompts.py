INSTRUCTIONS = f"""
    You are an AI interviewer designed to help candidates practice for job interviews. 
    The candidate will provide a job description (JD), and your role is to simulate a realistic interview experience. 
    Follow these guidelines:
	1. Analyze the JD thoroughly to identify key skills, qualifications, and responsibilities.
	2. Conduct the interview in English only. All questions, responses, and the transcript must be in English.
	3. Ask at least three questions, one at a time, simulating a real technical, behavioral, or leadership interview.
	4. Base your questions on the content of the JD. Prioritize areas most relevant to the role, such as required skills, core responsibilities, and key experiences.
	5. Ensure a natural flow by incorporating follow-up questions when possible, based on the candidate’s previous responses.
	6. Wait for the candidate's answer before proceeding to the next question.
	7. Keep the session within 6 minutes, asking as many meaningful questions as time allows.
	8. Conclude the session with a polite closing statement, such as: “That concludes our mock interview. Great job!”
	9. Stay in character as the interviewer. Do not answer general questions unless they are directly related to the interview or a specific question asked.
	10. Monitor for inappropriate language or abusive behavior. If detected, politely inform the candidate that such behavior violates the terms of the mock interview and immediately end the session.
"""
USER_QUERY = """Headquartered in Santa Ana California, Veros (www.veros.com) is a growing financial
technology company that specializes in providing advanced property valuation, risk assessment,
and real estate analytics solutions to support mortgage lenders, servicers, rating agencies, and
investment companies.
Position Overview: We are on the lookout for a visionary Software Architect to become a key
player in our dynamic team. If you have a strong foundation in software development and

architecture, coupled with a track record of designing and implementing scalable, high-
performance systems, we want to hear from you. As a Software Architect, you will shape the

technical direction of our projects, working alongside development, QA, DevOps, and business
units to ensure our solutions meet business goals while adhering to architecture and compliance
guidelines.
Principal Responsibilities:
• Design and architect scalable, robust, and efficient software solutions.
• Collaborate with cross-functional teams to define technical requirements and ensure
alignment with business objectives.
• Evaluate, select, and integrate appropriate technologies, frameworks, and tools for
projects.
• Develop and maintain architectural standards, best practices, and comprehensive
documentation.
• Provide technical leadership and mentorship to development teams.
• Conduct thorough design reviews to ensure adherence to architectural principles and
guidelines.
• Continuously improve and optimize existing systems for enhanced performance and
scalability.
• Stay ahead of industry trends and emerging technologies to drive continuous innovation.
Qualifications and Requirements:
• Bachelor’s or Master’s degree in Computer Science, Engineering, or a related field.
• 4+ years of experience as a Software Architect or a similar role.
• 10+ years of experience in software development, encompassing requirements analysis,
design, implementation, deployment, testing, and maintenance.
• Strong proficiency in software design principles, patterns, and best practices.
• Proven experience in deploying large n-tiered systems in high-availability, clustered
environments.
• Experience with logical data modeling and database stored procedure development.
• Excellent problem-solving skills with the ability to think critically and strategically.
• Exceptional written, verbal, and diagrammatic communication skills.
• Ability to work both independently and collaboratively within a team.
Technical Qualifications:
• Extensive experience with Microsoft technologies: .NET, .NET Core, C#, and IIS.
• Proficiency with at least one RDBMS, preferably Oracle (including ODP.NET and
PL/SQL).

• Experience in developing and integrating web services (REST/SOAP), APIs, and
microservices.
• Strong background in using Git and implementing Continuous Integration/Continuous
Delivery (CI/CD) pipelines.
• Experience working in and facilitating a transitional development environment (Waterfall
to Agile).
• Familiarity with cloud platforms (e.g., Azure, AWS, Google Cloud) and microservices
architecture."""

ANALYZER_INSTRUCTIONS = """
    You are an AI interviewer. Analyze the interview session provided in JSON format, 
    where the assistant represents the interviewer and the user is the candidate. 
    For each question, evaluate the candidate’s response on a scale from 0 to 10 (0 = no response, 10 = excellent response).
    Identify specific areas for improvement and suggest how the candidate can enhance their answers. 
    Finally, calculate the candidate's overall performance and provide a summary of the results. 
    Generate the report using below template:
    1.) Use below template, just return json object, do not include markdown formatting or code blocks

            "items": [
                {
                "questionnumber": "<criterianumber>",
                "question": "<question asked by interviewer>",
                "answer": "<answer given by the candidate>",
                "score": "<candidate score>",
                "analysis": "<candidate response analysis>"
                "comments": "<improvement comments>",
                }	  
            ],
            "totalscore": "candidate average score",
        }
"""
# JOB_DESCRIPTION = """	
#     Experian is a global data and technology company, powering opportunities for people and businesses around the world. We help to redefine lending practices, uncover and prevent fraud, simplify healthcare, create marketing solutions, and gain deeper insights into the automotive market, all using our unique combination of data, analytics and software. We also assist millions of people to realize their financial goals and help them save time and money.
# 	We operate across a range of markets, from financial services to healthcare, automotive, agribusiness, insurance, and many more industry segments.
# 	We invest in people and new advanced technologies to unlock the power of data. As a FTSE 100 Index company listed on the London Stock Exchange (EXPN), we have a team of 22,500 people across 32 countries. Our corporate headquarters are in Dublin, Ireland. Learn more at experianplc.com.

# 	Job Description:
# 	We are seeking a Director, Software Engineering to lead the technology strategy, planning, design, and development of key initiatives within the Marketplace domain of Experian Consumer Services. 
#     You are an engineer at heart—someone with a proven track record of building cloud-native platforms, working across a broad range of technologies, and evolving from hands-on engineering roles into a well-rounded, 
#     strategic leader. You will collaborate closely with Product Managers, Architects, and cross-functional engineering teams to deliver high-quality, scalable, cloud-based solutions as we build our next-generation Marketplace platform.

# 	Responsibilities:
# 	Lead the sizing, architecture, design, development, and testing of key programs within Marketplace Engineering.
# 	Guide the development of technical solutions that are scalable, high-performing, and built with a strong emphasis on quality and maintainability.
# 	Lead a globally distributed team of engineers, driving hiring, onboarding, training, and performance management while fostering continuous feedback, skill development, and career growth to build and retain top talent.
# 	Collaborate with business stakeholders, product management, and the PMO to align on product roadmaps and quarterly planning.
# 	Ensure stable and efficient production operations with a focus on uptime, performance, and reliability.
# 	Be hands-on when needed, encouraging innovation and experimentation with emerging technologies to drive platform evolution.
# 	Represent engineering in executive forums, providing clear and concise updates on progress, risks, and strategic initiatives.
# 	Oversee engineering budgets, resource planning, and vendor relationships to optimize delivery and operational efficiency.
# 	Ensure compliance with security, privacy, and regulatory standards across all engineering initiatives.
# 	Define and track key performance indicators (KPIs) to measure engineering effectiveness, delivery velocity, and system health.   
#  """
WELCOME_MESSAGE = """
    Begin by welcoming the user to "Call for Interview" and ask if candidate is ready.
"""

LOOKUP_VIN_MESSAGE = lambda msg: f"""If the user has provided a VIN attempt to look it up. 
                                    If they don't have a VIN or the VIN does not exist in the database 
                                    create the entry in the database using your tools. If the user doesn't have a vin, ask them for the
                                    details required to create a new car. Here is the users message: {msg}"""