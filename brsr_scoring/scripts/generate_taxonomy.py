import json
import os

raw_text = """
1. What is the scope 1 and scope 2 emissions intensity for the current year?
2. What is the scope 3 emissions intensity for the current year?
3. What was the Total Scope 1 and 2 intensity (Current Year) (Unit: Metric Tonne) - Physical Output?
4. What is the scope 1 and scope 2 emissions intensity in terms of purchasing power parity for the current year?
5. What are the total PM emissions for the Current Year (Unit: Metric Tonne)?
6. What are the total SOx emissions for the Current Year (Unit: Metric Tonne)?
7. What are the total NOx emissions for the Current Year (Unit: Metric Tonne)?
8. What is the water intensity per rupee of turnover in crores for the Current Year? (in kilolitres)
9. What is the % of untreated water discharge?
10. What is the total volume of fresh water withdrawal (in kilolitres) for the Current Year?
11. What is the total volume of fresh water discharge (in kilolitres) for the Current Year?
12. What is the total volume of water consumed (in kilolitres) in areas of water stress for the Current Year?
13. What is the total effluent discharge in the Current Year?
14. How much was the Water intensity in Current Year (in kilolitres) for physical output?
15. What is the water intensity per rupee of turnover adjusted for Purchasing Power Parity in crores Current Year (in kilolitres) - PPP?
16. What is the energy intensity turnover for the current year?
17. Percentage of energy consumed from renewable sources?
18. What is the energy intensity in terms of physical output?
19. What is the energy intensity adjusted for Purchasing Power Parity for Current Year?
20. What is the waste intensity adjusted for Purchasing Power Parity for Current Year?
21. How much was the hazardous waste for the current year (in metric tonnes)?
22. What is the waste recycled/recovered intensity for the current year?
23. Percentage of recycled or reused input material used in production (for manufacturing industry) or providing services (for service industry)
24. What was the total waste intensity (current year) (Unit: Metric Tonne) - Physical Output?
25. What is the waste intensity adjusted for Purchasing Power Parity for the current year?
26. Turnover of products and/or services as a percentage of turnover from all products/service that carry information about the safe and responsible usage?
27. What is the clinker factor ratio?
28. What is fly ash % utilisation in current year?
29. Is the company investing in new generation aircraft fleet? Has the number increased as compared to previous year?
30. What percentage of the total virgin raw material does the company produced and/or purchased covered by FSC, PEFC and/or SFI certification?
31. Total Lost time incident rate (LTIR)_Workers?
32. Total Lost time incident rate (LTIR)_Employees?
33. Total recordable work related injuries for employees as a % of the total employees in the company
34. Total recordable work related injuries for workers as a % of the total workers in the company
35. Fatalities of employees
36. Fatalities of workers
37. Count of high consquence work related injury or ill health of employees (excluding fatalities)
38. Count of high consquence work related injury or ill health of (excluding fatalities)
39. Percentage of plants and offices that were assessed (by entity or statutory authorities or third parties) with respect to health and safety practices?
40. Provide percentage of total employees covered under health and safety measures training
41. Percentage of total permanent employees covered by health insurance
42. Percentage of total other than permanent employees covered by health insurance
43. Percentage of total permanent workers covered by health insurance
44. Percentage of total other than permanent workers covered by health insurance
45. Percentage of total permanent employees covered by accident insurance
46. What is the percentage of female employees in the workforce
47. What is the turnover rate for permanent female employees in the Current Year
48. What is the turnover rate for permanent female worker in the Current Year
49. Pay parity between male and female employees
50. Number of complaints on PSH as a % of female employees/workers for current year
51. What is the gross wages paid to females as percentage of wages paid
52. How many complaints were filed on discrimination at workplace in current year?
53. How many complaints were filed by employees and workers or employees as a % of number of employees in the current year
54. What is the number of pending/unresolved employees and workers grievances as % of total complaints filed in the current year
55. How many complaints were filed on wages in the current year
56. Pending resolution of complaints as a % of total complaints filed by employees and workers pertaining to working conditions
57. What is the turnover rate for permanent workers for the Current Year
58. What is the turnover rate for permanent employees for the Current Year
59. What is the percentage of cost incurred as a % of total revenue of the company with regards to spending on measures towards wellbeing of employees and workers?
60. Percentage of workers or employees in association(s) or unions recognised by the listed entity
61. What is the number of complaints filed by the customers as a % of revenue in Current Year?
62. Total instances of product recalls
63. % of value chain partners (by value of business done with such partners) that were assessed for Health and Safety practices?
64. What is the purchases from trading houses % of total purchases
65. What is purchases from top 10 trading houses as % of total purchases from trading houses
66. Number of complaints filed by community stakeholders
67. Count of pending/unresolved communities grievances
68. Percentage of CSR obligation spent (CSR spent/CSR obligation)
69. What is the input material directly sourced from MSMEs/small producers (in % terms - As % of total purchases by value)
70. Percentage of capital expenditure investments in specific technologies to improve the environmental and social impacts of products and processes to total capex
71. What is the input material sourced directly from within India as % of total purchases
72. What is the % of job creation in smaller towns - wages paid to persons employed in smaller towns (permanent or non-permanent / on contract) as % of total wage cost
73. What are the number of days of account payable?
74. What is the sales to dealers/distributors as % of total sales
75. What is the sales to top 10 dealers/distributors as % of total sales to dealers/distributors
76. % of data breaches involving PII data of customers
77. Share of buildings that are certified according to international building standards/GRESB/IGBC
78. Percentage of independent directors on the board
79. Number of independent women directors on the board
80. Number of women directors on the board
81. Average attendance for board meeting in the current FY
82. Number of directorships of all board members
83. Number of directors against whom disciplinary action was taken by any law enforcement agency for the charges of bribery/corruption
84. Number of complaints received in relation to issues of conflict of interest of the directors/KMPs
85. Percentage of independent directors in nomination and remuneration committee
86. Percentage of independent directors in audit committee
87. Number of independent directors in risk management committee
88. Number of independent directors in CSR committee
89. Percentage of subject matter experts appointed in the Audit Committee
90. Ratio of remuneration of MD/CEO to median remuneration of employees
91. Percentage of non audit fees as compared to total audit fees
92. Number of whistle blower complaints filed in the current year
93. Number of pending consumer compliant on unfair trade practices
94. Number of employees against whom disciplinary action was taken by any law enforcement agency for the charges of bribery/corruption
95. Number of workers against whom disciplinary action was taken by any law enforcement agency for the charges of bribery/corruption
96. What is the share of RPTs (as respective %age) in purchases
97. What is the share of RPTs (as respective %age) in sales
98. What is the share of RPTs (as respective %age) in loans and advances
99. What is the share of RPTs (as respective %age) in investments
100. Are there any initiatives towards reduction in GHG emissions
101. What are the VOC/POP/HAP emissions for the current year (Unit: Metric Tonne)
102. What are the initiatives taken to reduce the NOx, SOx, PM, VOC, HAP and POP air emissions 
103. Does the company have facilities/operations in water stress regions
104. Has the entity implemented mechanism for Zero Liquid Discharge
105. Does the company monitor Chemical Oxygen Demand during water discharge
106. Third party verification of water data
107. What are the goals/targets/commitments towards Energy consumption
108. Does the entity have any sites/facilities identified as designated consumers under the Performance, Achieve and Tade Scheme of the Government of India? (Y/N) If yes, disclose whether targets set under the PAT scheme have been achieved in case targets have not been achieved, provide the remedial action taken, if any
109. Is there a disclosure regarding the energy management system? ISO 50001 Certification
110. Waste management practices and strategies to reduce usage of hazardous and toxic chemicals from the products and processes
111. What are the processes to safely reclaim the products for reusing, recycling and disposing at the end of life for, (a) Plastics (including packaging) (b)e-waste (c) hazardous waste and (d) other waste?
112. Whether Extended Producer Responsibility (EPR) is applicable to entity’s activities (Y/N). If yes, whether the waste collection plan is in line with the Extended Producer Responsibility plan submitteed to Pollution Control Boards
113. Third party verification of waste data
114. Is there presence of offices/manufacturing facilities in ecologically sensitive areas
115. Provide details of significant direct and indirect impact of the entity on biodiversity in ecological sensitive areas along with prevention and remediation activities
116. Does the company have an Environment or a Biodiversity policy
117. Does the company’s policy on Biodiversity extend to its value chain partners (Y/N)
118. Does the company take initiatives with regards to its Biodiversity conservation/land rehabilitation and biodiversity restoration
119. Are there any goals/targets/commitments set towards carbon neutrality/ Net Zero
120. Does the organisation report on CDP Disclosure as per Climate Change Module
121. Does the company perform climate related scenario analysis (based on TCFD framework); Based on the climate risk assessment, has the company set up a plan to adapt to the identified physical climate risks 
122. Presence of ISO 14001:2015 certifications
123. Does the entity implement carbon pricing mechanism/model?
124. Does the company have a policy on environmental management and is it available publicly
125. Is the entity compliant with the appliacble environmental law/regulations/guidelines for India; such as the Water (Prevention and Control of Pollution) Act, AIr (Prevention and Control of Pollution) Act, Environmental protection act and rules thereunder (Y/N). If not, provide details of all such non compliances
126. Does the company have a strategy for climate change adaptation and mitigation
127. Discussion of the integration of environmental considerations into strategic planning for data centre needs
128. Are there any social or environmental concerns and/or risks arising from production or disposal of products, as identified in the Life Cycle Perspective/Assessments
129. Has the company taken initiatives to use reusable, recyclable or compostable packagin
130. What are the intiatives taken to reduce plastic packaging
131. Turnover of products and/or services as a percentage of turover from all products/service that carry information about the recycling and/or safe disposal
132. Does your company have a publicly available no deforestation policy or commitment that applies to your company’s operational practices
133. Does the company owns/lease/manages forest land for its operations
134. Are there any intiatives taken with respect to sustainable agriclutire by the company
135. Is the manufacturing smart farm equipments/machinery
136. Is the company exposed to animal products and are these certified or accredited by one or more independent third party? If yes, does the company demand or monitor such certification or accreditation from its suppliers?
137. What are the initiatives taken with respect to Chemical Sagety management
138. Does the company have waste heat recovery systems for enchancing energy efficiency (Cement)
139. Is the forestland certified as per international sustainable forest management standards such as FSC, PEFC, SFI
140. What measures are taken to reduce marine pollution and manage ballast water
141. Does the company comply with new regilation of Energy Efficiency Existing Ship (require al ships above 400GT)
142. Are there any initiatives to promot sustainable shipping practices or reduce the carbon footprint of port operations
143. Does the copmany manufacture electric or alternate fuel bsaed vessel/ships or related components for the same?
144. Is company using sustainable alternative fuels liek SAF in its fleet
145. Is there any commitment or plan to shift to alternate fuels such as SAF
146. Has the company partnered with airframe and tehnology manufacturesre to increase fuel efficiency and reduce environmental impact
147. Does the company measure or track the age of aircrafts? If yes, the what is the average of company’s air fleet
148. Does the company monitor and measure noise levels? Are they compliant with noise regulations
149. Does the company’s policy and measures align with International Civil Aviation Organisation’s Balance Approach
150. Does the company have oil spill/gas leak action plan
151. Did the company experience any spills for the current and previous years
152. Does the entity have a system to finance sustainable projects
153. Are ESG factors incorporated in the lending and investment decisions
154. Does the company follow sustainable mining practices
155. Does the company have tailing management system after mining
156. Does the company have a publicly available policy in place for mining from conflict affected and high risk areas. If yes, provide details
157. Does the company undertake intiatives or programs to raise awareness about sustainability challenges and opportunities in the natural rubber industry for suppliers
158. What measures are in palce to ensure public sagety and security at facilities?
159. How are potential security threats and emergencies addressed
160. Is the company using low carbon vehicle and equipments in its ports to carry out operations
161. Are the ESG related factors being monitored in investee companies/lending processes
162. Does the company lend towards Electric Vehicles
163. Does the company have ESG related products/services?
164. Does the company integrate ESG aspects in its insurance underwriting process for non life non health insurance reinsurance
165. Does your company offer eSG based products within its non life non health insurance business segment
166. Does the company participate in the GRESB for real estate benchmark assessment
167. Is the company currently operating/deploying low carbon fleet (EVs or other vehicles) in its logistics business or do they have a plan to shift current feet to low carbon alternative fleet
168. Does the company have End of Life Vehicles management
169. What steps are taken by the company to mitigate any potential health impacts of tyre and rubber product manufacturing on local communities
170. Does the company have a strategy or initiative in place to enourage small forest owners and timber suppliers to adopt best practices or sustainable management in order to obtain certification from recognized systems such as PEF, FSC or equivalent
171. Does the company have commitment in place integrating circular fashin into all its operations? If yes, provide details
172. Does the company manufacture/sell sustainable apparel or garments
173. Is the company using sustainable material in its typre (also state the ttype of material used) or has committed to use sustainable material in typres
174. Is the company manufacturing sustainable/eco-friendly paint/coatings
175. Is the company manufacturing any energy efficient products or is spending on R&D for manufacturing such products in near future?
176. Is the company fulfilling International Maritime Organisation - MARPOL Air Pollution prevention guidelines 
177. Whether an occupational health and safety management system is implemented by the entity
178. What are the processes used to identify work-related hazards and assess risks on a routine and non routine bassi by the entity
179. Does the company have processes for workers to report the work related hazards and to remove themselves from such risks (Y/N)
180. Was there training given to workers on health and sagety measures in Current Year
181. Does the company mention that they have a safety committee/policy in place with respect to accidents or misfortune events 
182. Does the entity have ISO 45001:2018 certification
183. Are the entity’s manufacturing facilties WRAP certified
184. Does the company have a target to achieve gender diversity in the workforce
185. Does the company have a diversity equality and inclusion policy
186. Does the company have policy for precention to prevent sexual harassment at workplace
187. Are all complaints filed by the employees during current fiscal year closed
188. Does the company have a human rights policy established
189. Does the company provide medical assistance (Ambulance service, fixed medical checkups, to the employees)
190. Does the company take measures for the well being of individuals other than permanent employees (which may include interns, contracts, etc.)
191. Does the organisation have opportunities for Paternal leavesWhat all initiatives does the organisation undertake for increase in the retention rate of employees
192. Does the company have employe development programs that have been developed to upgrade and improve employee skills
193. Did the company face any strike in the current year
194. Does the company conduct an employee satisfaction survey
195. Does the company have policy on offering stock options
196. Does the company have mechanisms to receive and respond to consumer complaints and feedback
197. Did your entity carry out any survey with regard to consumer satisfaction relating to the major products/services of the entity, significant locations of operation of the entity or the entity as a whole
198. Steps taken to inform and educate consumers about safe and responsible usage of products and/or service
199. ISO 9001:2015 certification
200. Does the entity display product information on the product over and above what is mandated as per local laws
201. When the onboarding of new vendors takes place, does the company have their supplier code of conduct designed
202. Disclose any significant adverse impact on the environment arising from the value chain of the entity. Are there any mitigations or adaptiation measures taken by the entity in this context
203. Provide details of any corrective actions taken or underway to adderss significant risks/concerns arising from asessment of health and safety practices practices and working conditions of value chain partners
204. Does the entity have procedures in place for sustainable sourcing strategy around sustainable/efficient/responsible supply chain
205. Is there a robust supplier assessment done by the company to avoid any conflicts with ESG requirements/sustainability/ESG assessment for suppliers
206. Does the company have a documented CSR policy in place
207. Whether there are mechanisms to receive and redress grievances of the community
208. Does the entity disclose the details of beneficiaries of CSR projects
209. Does the company conduct impact assessments for CSR projects? If yes, provide details
210. Does the company conduct of assessment of negative impacts of its operation on the communities
211. Provide details of actions taken to mitigate any negative social impacts identified in the Social Impact Assessments
212. Does the entity have a framework/policy on cybersecurity and risks related to data privacy
213. Does the company’s policy on cybersecurity and risks related to data privacy extend to its value chain partners
214. Provide number of instances of data breaches along with their impact on the company
215. Does the company conduct cybersecurity assessment by a third party
216. Does the entity comply with ISO 27001:2013, ISO 22301:2019 OR PCI DSS standards to safeguard the customer data
217. Does the organisation conduct training on data privacy and awareness programs for information security to its customers/employees
218. Does the company have a communication plan for engaging with the communities affected with aircraft noise
219. Does the company comply with Maritime Labour Convention adopted by International Labour Organisation in 2006
220. Is the company’s training centre for its seafarers certified or has got validated by any institution
221. Does the company have agreements which safeguard the wellbeing of farm workers through the Agricultural Labour Practices Code
222. Does the company ensure its jewellery meet BIS hallmark standards for quality assurance
223. Is the education institute providing placement assistance to its students
224. Does the company have a editorial policy
225. Does the company implement strategies to control and reduce the amount of construction and demolition waste from buildings that are constructed or are part of portfolio
226. Does the company have programs established to measure food loss and waste
227. Does the company have any targets to reduce food waste
228. What initiatives are undertaken to mitigate the health risks of smoking and tobacco use
229. Are any of its hospitals accredited with NABH or JIC? How many of its hospitals accredited with NABH or JIC? 
230. Does the company have a program or is taking efforts to increase the availability and affordability of the medicines in low income/developing markets 
231. Does the company have publicly available programs to improve the accessibility to healthcare
232. Are the production units and R&D centres certified to International Aerospace Standard AS9100D and other required aviation standards
233. Has the company identified risk and threats it faces in ensuring the safet and security of its passengers, staff, and assets
234. Does the company collaborate with external agencies to reduce the amount of food loss and waste
235. Is the company promoting local tourism
236. Does the company actively engage in the research collaborations with the universities, research institutions and other companies
237. Provide details on development of clinical technology, clinical capabilites and programmes
238. Does the entity have system/mechanism in place to address issues (congestion, indoor coverage, call drops, modernisation and upgrade of data speeds, among others)
239. Does the company have digital/smart substations or plans to have it in future? (If yes, provide the number of substation)
240. Does the company use smart metters in its distribution grid
241. Does the company have inhouse research and development facilities/centres and team
242. Is the company offering e-learning courses/certifications to its students
243. ISO 22000 FSSC
244. Does the company confirm on its commitments to follow guidelines provided by FSSAI and NIN
245. Does the company conduct food safety audits
246. Does the company mention use of natural ingredients in their products and are they approved by government norms
247. does the company have a policy on ingredient safety? is there any mention of use of paraben in the products
248. ISO 13485
249. Does the company have a policy for ensuring quality and patient safety during clinical trials
250. Does the entity display relevant information on the product labels as per the requirements of national and international drug regulatory bodies
251. How many labs are NABL accredited
252. How did the entity handle aliquots and provide details on reducing aliquots
253. Does the company have a dedicated ethics committee to oversee all the clinical trials
254. Does the company have a public policy committing it and/or its suppliers to animal welfare principles
255. Does the company meet priority sector lending requirements as per RBI
256. Does the entity have a plan to lend to MSME? If yes, provide details
257. Does the company have a policy or commitment on financial inclusion
258. Does the company have programmes for listing designed to promote small businesses (MSME) and community development
259. Does the company index for social enterprises that target underserved or less privileged population segments
260. Does the company have its products in compliance with BIS standards
261. Is the company adhering to Food Safety Standards and Processes
262. Description of actions and initiatives to promote access to healthcare products for priority diseases
263. Does the company focus on providing healthcare facilities to vulnerable portions of the population
264. N-CAP Rating of 4 or 5 star?
265. Is the company sourcing raw materials from the certified sustainable sources (such as global GAP, RSPO, Rainforest, FSC)
266. Do the farmers have access to PPE kits to prevent themselves from exposure to pesticides while handling wet green tobacco leaves which could lead to Green Tobacco Sickness
267. Does the company have any standards or programmes related to sustainable tobacco during their supply chain process
268. Are there any technicians appointed during the supply chain process to detect or monitor the agriculture or crop management process
269. Existence of management process for ensuring quality and patient safety during clinical trials
270. Provide information on project(s) for which ongoing Rehabilitation and Resettlements is being undertaken by the company
271. How many patents were filed and granted during the current year
272. Does the company have due diligence process for sourcing minerals as raw materials
273. Has the entity performed audit by DoT and maintain compliance with EMF radiation levels set by local regulations and ICNIRP
274. Does the organisation have Board Diversity Policy
275. Presence of policy on appointment and reappointment of board of directors
276. Is the chairperson of the board an independent director?
277. Does the company have separate roles for Chairman and CEO
278. Does the company have lead independent director on the board
279. Does the company ensure effectiveness of the board through internal or external evaluation or assessment
280. Does the company have processes in place to avoid/manage conflicts of interest involving members of the Board
281. Does the company conduct training and awareness programmes on any of the NGBRC principles for BOD
282. Independence of Chairperson of committee (risk management)
283. Independence of Chairperson of committee (NRC)
284. Independence of Chairperson of committee (Audit)
285. Is there a claw back mechanism/policy for senior management/KMP
286. Is the independent director paid commissions/incentives other than the board sitting fees
287. Is the variable pay of executives linked to sustainability or ESG parameters
288. Does the company have a policy for appointment or reappointment o auditors
289. Discontinuation of auditors before end of term
290. Does the entity have a whistleblower policy
291. Is the whistleblower policy applicable to value chain
292. Does the entity have an anti corruption or anti bribery policy
293. Does the company have code of conduct policy
294. Does the company have a policy on anti-money laundering and/or insider trading/dealing
295. Does the company provide training on code of conduct, anti corruption, and anti bribery policies to the employee
296. How does the company ensure that the minority shareholders effectively protect their interest and rights within company
297. Has the company undergone any fines/penalties/punishments/award/compunding fees/settlement amount paid in proceedings with regulators/law enforcement agencies/judicial institution during the financial year
298. Does the company implement a comprehensive framework or Enterprise Risk Management framework
299. Has the company taken any corrective action or underway on any issues related to anti competitive model, based on adverse orders from regulatory authorities? If yes, provide details
300. Does the entity have a business continuity and disaster management plan
301. Does the company have ESG or Sustainability or BRSR policy
302. Does the company perform materiality assessment and identify material ESG issues
303. Does the company conduct assurance for its ESG or sustainability data through a third party or external agency
304. Does the company conduct assurance for its suppliers’ ESG or sustainability data through a third party or external agency
305. Does the company have a highest authority responsible for implementation and oversight of the Business Responsibility(ies) and ESG policy
306. Does the company have a specified committee of the board/director responsible for decision making on sustainability related issues (Y/N)
307. Were there any promotor sponsored resolutoins that were defeated during the current FY
308. Does the company follow GRI standards
309. Is the company aligned with SDGs? Does the company set targets according  to SDGs
310. Is your company a signatory/participant of the United Nations Global Compact
311. Does the company have affiliatoins with trade and indsutry chambers/associations
312. Has the company advocated any public policy positions? If yes, provide details
313. Does the company disclose ESG engagement with investee company
314. Does the entity have stewardship code
315. Is there a policy on related party transactions
316. Disclosure of transactions with related parties during the year which are more than 10% of the revenue
"""

taxonomy = {}
for line in raw_text.split('\n'):
    line = line.strip()
    if not line:
        continue
    # Extract number and text
    parts = line.split('.', 1)
    if len(parts) == 2:
        num = parts[0].strip()
        text = parts[1].strip()
        question_id = f"Q{num}"
        
        # very basic heuristic: if text asks for '%', 'count', 'number', 'intensity', 'rate', 'ratio', 'value', 'amount' -> numeric
        # if text asks 'does', 'is', 'has', 'whether' -> boolean
        # else string/text
        text_lower = text.lower()
        if any(w in text_lower for w in ['?', 'whether ', 'is ', 'does ', 'has ', 'are ', 'did ', 'presence ']):
            dtype = "boolean"
        elif any(w in text_lower for w in ['%', 'percentage', 'count', 'number', 'amount', 'intensity', 'rate', 'ratio', 'share', 'total', 'how much', 'how many', 'days', 'volume', 'value']):
            dtype = "numeric"
        else:
            dtype = "text"
            
        taxonomy[text] = {
            "question_id": question_id,
            "question_text": text,
            "data_type": dtype
        }

os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'config'), exist_ok=True)
with open(os.path.join(os.path.dirname(__file__), '..', 'config', 'taxonomy_map_full.json'), "w") as f:
    json.dump(taxonomy, f, indent=2)

print("Created taxonomy_map_full.json with", len(taxonomy), "questions.")
