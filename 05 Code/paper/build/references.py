"""Verified references (IEEE style). Journal metadata checked against Crossref DOI records on 4 Oct 2026;
official documents checked against the files in data/raw/ or the publisher's page (see reports/paper_references_verified.md).

Each entry: key -> (IEEE text with *italic* markers, why it is used, what it supports, verification note).
"""

REFS = {
    "mishra2010": (
        'A. K. Mishra and V. P. Singh, "A review of drought concepts," *J. Hydrol.*, vol. 391, no. 1–2, pp. 202–216, '
        "Sep. 2010, doi: 10.1016/j.jhydrol.2010.07.012.",
        "Standard review of drought definitions and impacts.",
        "Drought impacts arise from a deficit interacting with affected systems (Introduction).",
        "Crossref DOI record."),
    "wilhelmi2002": (
        'O. V. Wilhelmi and D. A. Wilhite, "Assessing vulnerability to agricultural drought: A Nebraska case study," '
        "*Nat. Hazards*, vol. 25, no. 1, pp. 37–58, Jan. 2002, doi: 10.1023/A:1013388814894.",
        "Classic indicator-based agricultural drought vulnerability study.",
        "Drought vulnerability depends on the exposed system; indicator approach to agricultural drought.",
        "Crossref DOI record."),
    "kumar2004": (
        'K. K. Kumar, K. R. Kumar, R. G. Ashrit, N. R. Deshpande, and J. W. Hansen, "Climate impacts on Indian '
        'agriculture," *Int. J. Climatol.*, vol. 24, no. 11, pp. 1375–1393, Sep. 2004, doi: 10.1002/joc.1081.',
        "Links Indian monsoon variability to agricultural production.",
        "Kharif agriculture depends on the monsoon; monsoon variability is reflected in crop production.",
        "Crossref DOI record."),
    "rasmusson1983": (
        'E. M. Rasmusson and T. H. Carpenter, "The relationship between eastern equatorial Pacific sea surface '
        'temperatures and rainfall over India and Sri Lanka," *Mon. Weather Rev.*, vol. 111, no. 3, pp. 517–528, '
        "Mar. 1983, doi: 10.1175/1520-0493(1983)111<0517:TRBEEP>2.0.CO;2.",
        "Foundational paper on the ENSO and Indian rainfall relationship.",
        "Warm Pacific (El Niño) conditions historically associated with below-normal Indian monsoon rainfall.",
        "Crossref DOI record."),
    "kumar2006": (
        'K. K. Kumar, B. Rajagopalan, M. Hoerling, G. Bates, and M. Cane, "Unraveling the mystery of Indian monsoon '
        'failure during El Niño," *Science*, vol. 314, no. 5796, pp. 115–119, Oct. 2006, doi: 10.1126/science.1131152.',
        "Explains why some El Niño years cause monsoon failure and others do not.",
        "El Niño association with deficient monsoon; not every El Niño year is a drought.",
        "Crossref DOI record."),
    "kumar1999": (
        'K. K. Kumar, B. Rajagopalan, and M. A. Cane, "On the weakening relationship between the Indian monsoon and '
        'ENSO," *Science*, vol. 284, no. 5423, pp. 2156–2159, Jun. 1999, doi: 10.1126/science.284.5423.2156.',
        "Documents time variation of the ENSO-monsoon relationship.",
        "The ENSO-monsoon relationship has varied over time.",
        "Crossref DOI record."),
    "udmale2014": (
        'P. Udmale, Y. Ichikawa, S. Manandhar, H. Ishidaira, and A. S. Kiem, "Farmers\' perception of drought impacts, '
        'local adaptation and administrative mitigation measures in Maharashtra State, India," *Int. J. Disaster Risk '
        'Reduct.*, vol. 10, pp. 250–269, Dec. 2014, doi: 10.1016/j.ijdrr.2014.09.011.',
        "Maharashtra-specific drought impact study.",
        "Recurrent drought in Maharashtra; dependence on rainfed cropping and livestock.",
        "Crossref DOI record; abstract read."),
    "swami2021": (
        'D. Swami and D. Parthasarathy, "Dynamics of exposure, sensitivity, adaptive capacity and agricultural '
        'vulnerability at district scale for Maharashtra, India," *Ecol. Indic.*, vol. 121, Art. no. 107206, Feb. 2021, '
        "doi: 10.1016/j.ecolind.2020.107206.",
        "Closest prior district-level vulnerability study for Maharashtra.",
        "Some districts vulnerable despite low exposure (Introduction); equal-weight aggregation, 1966-2015 (Related Work).",
        "Crossref DOI record; abstract read."),
    "ipcc2001": (
        "J. J. McCarthy, O. F. Canziani, N. A. Leary, D. J. Dokken, and K. S. White, Eds., *Climate Change 2001: "
        "Impacts, Adaptation, and Vulnerability. Contribution of Working Group II to the Third Assessment Report of the "
        "Intergovernmental Panel on Climate Change*. Cambridge, U.K.: Cambridge Univ. Press, 2001.",
        "Source of the exposure, sensitivity and adaptive-capacity vulnerability framework.",
        "Vulnerability as a function of exposure, sensitivity and adaptive capacity.",
        "IPCC report front matter (ipcc.ch) lists editors and publisher."),
    "fussel2007": (
        'H.-M. Füssel, "Vulnerability: A generally applicable conceptual framework for climate change research," '
        "*Glob. Environ. Change*, vol. 17, no. 2, pp. 155–167, May 2007, doi: 10.1016/j.gloenvcha.2006.05.002.",
        "Conceptual framework for vulnerability.",
        "Vulnerability concepts; distinction between hazard and system characteristics.",
        "Crossref DOI record."),
    "chakraborty2016": (
        'A. Chakraborty and P. K. Joshi, "Mapping disaster vulnerability in India using analytical hierarchy process," '
        "*Geomat. Nat. Hazards Risk*, vol. 7, no. 1, pp. 308–325, 2016, doi: 10.1080/19475705.2014.897656.",
        "Indian district vulnerability mapping with expert (AHP) weights.",
        "AHP weighting in Indian studies; district vulnerability mapping with exposure, sensitivity, adaptive capacity.",
        "Crossref DOI record; abstract read."),
    "saha2021": (
        'S. Saha et al., "Spatial assessment of drought vulnerability using fuzzy-analytical hierarchical process: A case '
        'study at the Indian state of Odisha," *Geomat. Nat. Hazards Risk*, vol. 12, no. 1, pp. 123–153, 2021, '
        "doi: 10.1080/19475705.2020.1861114.",
        "Indian drought vulnerability with fuzzy AHP (subjective weights).",
        "AHP-based weighting rests on expert judgment.",
        "Crossref DOI record (8 authors, so et al.)."),
    "oecd2008": (
        "M. Nardo, M. Saisana, A. Saltelli, S. Tarantola, A. Hoffmann, and E. Giovannini, *Handbook on Constructing "
        "Composite Indicators: Methodology and User Guide*. Paris, France: OECD Publishing, 2008.",
        "Authoritative guide to composite indicators, PCA/FA weighting, retention rules and factorability checks.",
        "PCA weighting is a recognised option; sensitivity to small samples; KMO/Bartlett; retention rules; "
        "OECD/JRC factor weighting used as a sensitivity version.",
        "OECD/JRC publication pages; ISBN 978-92-64-04345-9; handbook read in the project (reports/pca_weighting_methods_report.md)."),
    "jolliffe2016": (
        'I. T. Jolliffe and J. Cadima, "Principal component analysis: A review and recent developments," *Phil. Trans. '
        'R. Soc. A*, vol. 374, no. 2065, Art. no. 20150202, Apr. 2016, doi: 10.1098/rsta.2015.0202.',
        "Standard PCA reference.",
        "PCA definition (eigen-decomposition of the correlation matrix); arbitrary component signs.",
        "Crossref DOI record."),
    "adger2006": (
        'W. N. Adger, "Vulnerability," *Glob. Environ. Change*, vol. 16, no. 3, pp. 268–281, Aug. 2006, '
        "doi: 10.1016/j.gloenvcha.2006.02.006.",
        "Review of vulnerability research.",
        "Vulnerability research separates hazard from system characteristics.",
        "Crossref DOI record."),
    "murthy2015": (
        'C. S. Murthy, B. Laxman, and M. V. R. Sesha Sai, "Geospatial analysis of agricultural drought vulnerability '
        'using a composite index based on exposure, sensitivity and adaptive capacity," *Int. J. Disaster Risk Reduct.*, '
        "vol. 12, pp. 163–171, Jun. 2015, doi: 10.1016/j.ijdrr.2015.01.004.",
        "Indian composite agricultural drought vulnerability index.",
        "Composite index from exposure, sensitivity and adaptive capacity with geospatial data (title-level claim only).",
        "Crossref DOI record."),
    "sharma2019": (
        'J. Sharma and N. H. Ravindranath, "Applying IPCC 2014 framework for hazard-specific vulnerability assessment '
        'under climate change," *Environ. Res. Commun.*, vol. 1, no. 5, Art. no. 051004, Jun. 2019, '
        "doi: 10.1088/2515-7620/ab24ed.",
        "Indian application of the IPCC vulnerability framework.",
        "IPCC framework applied to hazard-specific vulnerability (title-level claim).",
        "Crossref DOI record."),
    "nair2022": (
        'S. C. Nair and A. Mirajkar, "Drought vulnerability assessment across Vidarbha region, Maharashtra, India," '
        "*Arab. J. Geosci.*, vol. 15, no. 4, Art. no. 355, Feb. 2022, doi: 10.1007/s12517-022-09623-0.",
        "Maharashtra (Vidarbha) drought vulnerability study.",
        "Prior drought vulnerability assessment within Maharashtra (title-level claim).",
        "Crossref DOI record."),
    "cutter2003": (
        'S. L. Cutter, B. J. Boruff, and W. L. Shirley, "Social vulnerability to environmental hazards," *Soc. Sci. Q.*, '
        "vol. 84, no. 2, pp. 242–261, Jun. 2003, doi: 10.1111/1540-6237.8402002.",
        "Original Social Vulnerability Index (factor analysis).",
        "Factor-analysis-based vulnerability index.",
        "Crossref DOI record."),
    "abson2012": (
        'D. J. Abson, A. J. Dougill, and L. C. Stringer, "Using principal component analysis for information-rich '
        'socio-ecological vulnerability mapping in Southern Africa," *Appl. Geogr.*, vol. 35, no. 1–2, pp. 515–524, '
        "Nov. 2012, doi: 10.1016/j.apgeog.2012.08.004.",
        "PCA-based vulnerability mapping.",
        "PCA used for vulnerability mapping (title-level claim).",
        "Crossref DOI record."),
    "balaganesh2020": (
        'G. Balaganesh et al., "Development of composite vulnerability index and district level mapping of climate '
        'change induced drought in Tamil Nadu, India," *Ecol. Indic.*, vol. 113, Art. no. 106197, Jun. 2020, '
        "doi: 10.1016/j.ecolind.2020.106197.",
        "Indian district drought vulnerability index with PCA weights.",
        "PCA weights for a district drought vulnerability index; classification by index magnitude.",
        "Crossref DOI record (7 authors, so et al.); abstract read."),
    "kim2021": (
        'J. E. Kim, J. Yu, J.-H. Ryu, J.-H. Lee, and T.-W. Kim, "Assessment of regional drought vulnerability and risk '
        'using principal component analysis and a Gaussian mixture model," *Nat. Hazards*, vol. 109, no. 1, '
        "pp. 707–724, Oct. 2021, doi: 10.1007/s11069-021-04854-y.",
        "PCA-based drought vulnerability with a clustering-type model.",
        "PCA combined with a Gaussian mixture model for drought vulnerability and risk (title-level claim).",
        "Crossref DOI record."),
    "pinzon2026": (
        'C. E. Pinzón Flórez, M. Díaz, L. G. Echeverry, and G. Escobar Morales, "Designing a territorial composite '
        'vulnerability index to guide public health action in Cali, Colombia," *PLOS One*, vol. 21, no. 1, '
        "Art. no. e0332486, Jan. 2026, doi: 10.1371/journal.pone.0332486.",
        "Applied example of eigenvalue-weighted absolute-loading indicator weights.",
        "Indicator weights from eigenvalues and absolute loadings.",
        "Crossref DOI record; methods section read in the project."),
    "kaiser1974": (
        'H. F. Kaiser, "An index of factorial simplicity," *Psychometrika*, vol. 39, no. 1, pp. 31–36, Mar. 1974, '
        "doi: 10.1007/BF02291575.",
        "Original KMO sampling-adequacy measure.",
        "KMO measure.",
        "Crossref DOI record."),
    "uzcategui2023": (
        'M. Uzcategui-Salazar and J. Lillo, "Assessment of social vulnerability to groundwater pollution using K-means '
        'cluster analysis," *Environ. Sci. Pollut. Res.*, vol. 30, no. 6, pp. 14975–14992, 2023, '
        "doi: 10.1007/s11356-022-22810-6.",
        "Example of K-Means used for vulnerability classification.",
        "K-Means classification of social vulnerability (title-level claim).",
        "Crossref DOI record (online 2022, issue 2023)."),
    "lloyd1982": (
        'S. Lloyd, "Least squares quantization in PCM," *IEEE Trans. Inf. Theory*, vol. 28, no. 2, pp. 129–137, '
        "Mar. 1982, doi: 10.1109/TIT.1982.1056489.",
        "Original K-Means (Lloyd) algorithm.",
        "K-Means minimizes within-cluster squared distance.",
        "Crossref DOI record."),
    "pai2014": (
        'D. S. Pai, M. Rajeevan, O. P. Sreejith, B. Mukhopadhyay, and N. S. Satbha, "Development of a new high spatial '
        "resolution (0.25° × 0.25°) long period (1901–2010) daily gridded rainfall data set over India and its "
        'comparison with existing data sets over the region," *Mausam*, vol. 65, no. 1, pp. 1–18, Jan. 2014, '
        "doi: 10.54302/mausam.v65i1.851.",
        "Reference publication for the IMD 0.25 degree gridded rainfall product.",
        "Rainfall data source.",
        "Crossref DOI record."),
    "vanoldenborgh2021": (
        'G. J. van Oldenborgh et al., "Defining El Niño indices in a warming climate," *Environ. Res. Lett.*, vol. 16, '
        "no. 4, Art. no. 044003, Apr. 2021, doi: 10.1088/1748-9326/abe9ed.",
        "Scientific basis of the relative Niño-3.4 index.",
        "RONI compares Niño-3.4 with the tropical mean so warming does not inflate it.",
        "Crossref DOI record (7 authors, so et al.)."),
    "noaaroni": (
        'NOAA Climate Prediction Center, "Relative Oceanic Niño Index (RONI), ERSST.v6." [Online]. Available: '
        "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt (accessed Sep. 27, 2026).",
        "ENSO data source.",
        "RONI values used for the slope and El Niño years.",
        "File in data/raw/enso/ with URL and SHA-256 in source_manifest.csv."),
    "noaaannounce": (
        'NOAA Climate Prediction Center, "CPC adopts Relative Oceanic Niño Index (RONI) for reliable, responsive '
        'monitoring and tracking of ENSO," Feb. 2026. [Online]. Available: '
        "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/announcement.php (accessed Sep. 27, 2026).",
        "Official adoption of RONI.",
        "RONI became NOAA's official ENSO index in February 2026.",
        "HTML snapshot in data/raw/enso/cpc_roni_announcement_page.html."),
    "census2011": (
        "Office of the Registrar General and Census Commissioner, India, *Census of India 2011: Primary Census "
        "Abstract*. New Delhi, India: Ministry of Home Affairs, Government of India, 2011. [Online]. Available: "
        "https://censusindia.gov.in",
        "Socioeconomic data source.",
        "Agricultural-worker share and literacy.",
        "Workbook in data/raw/census/; exact download URL NOT VERIFIED, so the portal home page is cited."),
    "censusvd": (
        "Office of the Registrar General and Census Commissioner, India, *District Census Handbook, Maharashtra: "
        "Village Directory (Census of India 2011)*. New Delhi, India, 2011. [Online]. Available: "
        "https://censusindia.gov.in/nada/index.php/catalog/830",
        "Irrigation data source.",
        "Rainfed share of net sown area.",
        "URL recorded in source_manifest.csv."),
    "agcensus2014": (
        "Commissionerate of Agriculture, Government of Maharashtra, *Agriculture Census 2010-11 (Phase I): Maharashtra "
        "State Report*, 2014. [Online]. Available: https://krishi.maharashtra.gov.in/Site/Upload/Pdf/Publications/Argi.pdf",
        "Landholding data source.",
        "Small-holding share.",
        "URL and publisher recorded in source_manifest.csv."),
    "soi": (
        'Survey of India, "Administrative Boundary Database, Maharashtra (OVSF/1M/8)," Survey of India Online Maps '
        "Portal. [Online]. Available: https://onlinemaps.surveyofindia.gov.in",
        "Boundary data source.",
        "District polygons for rainfall aggregation and maps.",
        "ZIP in data/raw/boundaries/; portal URL in source_manifest.csv."),
    "gr2018": (
        "Revenue and Forest Department, Government of Maharashtra, \"Declaration of drought in talukas of the state in "
        "the kharif season of 2018,\" Government Resolution, GR code 201810311722349219, Oct. 31, 2018 (in Marathi). [Online]. "
        "Available: https://gr.maharashtra.gov.in/Site/Upload/Government%20Resolutions/Marathi/201810311722349219.pdf",
        "Validation data, 2018.",
        "151 talukas declared (final declaration).",
        "PDF in data/raw/validation/; header read (number, date, department). Title translated from Marathi."),
    "gr2023": (
        "Revenue and Forest Department, Government of Maharashtra, \"Declaration of drought in talukas of the state in "
        "the kharif season of 2023,\" Government Resolution, GR code 202310311545053419, Oct. 31, 2023 (in Marathi). [Online]. "
        "Available: https://gr.maharashtra.gov.in/Site/Upload/Government%20Resolutions/Marathi/202310311545053419.pdf",
        "Validation data, 2023.",
        "40 talukas declared in the main order.",
        "PDF in data/raw/validation/; header read. Title translated from Marathi."),
    "gr2026": (
        "Relief and Rehabilitation Department, Government of Maharashtra, \"Declaration of drought and relief measures "
        "in 265 talukas under Trigger-1 in the kharif season of 2026,\" Government Resolution, GR code "
        "202609261117494941, Sep. 25, 2026 (in Marathi). [Online]. Available: "
        "https://gr.maharashtra.gov.in/Site/Upload/Government%20Resolutions/Marathi/202609261117494941.pdf",
        "Holdout validation data, 2026.",
        "265 talukas declared at Trigger-1.",
        "PDF in data/raw/validation/; header read. Title translated from Marathi."),
    "dmm2016": (
        "Department of Agriculture, Cooperation and Farmers Welfare, *Manual for Drought Management*. New Delhi, India: "
        "Ministry of Agriculture and Farmers Welfare, Government of India, Dec. 2016.",
        "Official drought declaration procedure cited in the GRs.",
        "GRs follow the staged procedure of the 2016 manual (Trigger-1, Trigger-2, declaration).",
        "Publisher and date confirmed via search results; the 2018 GR preamble cites the 2016 manual."),
    "pedregosa2011": (
        'F. Pedregosa et al., "Scikit-learn: Machine learning in Python," *J. Mach. Learn. Res.*, vol. 12, '
        "pp. 2825–2830, 2011.",
        "Software used for StandardScaler, PCA and K-Means.",
        "Implementation of the pipeline.",
        "JMLR page jmlr.org/papers/v12/pedregosa11a.html."),
    "kaiser1960": (
        'H. F. Kaiser, "The application of electronic computers to factor analysis," *Educ. Psychol. Meas.*, vol. 20, '
        "no. 1, pp. 141–151, Apr. 1960, doi: 10.1177/001316446002000116.",
        "Origin of the eigenvalue-greater-than-one rule.",
        "Kaiser retention criterion.",
        "Crossref DOI record."),
    "horn1965": (
        'J. L. Horn, "A rationale and test for the number of factors in factor analysis," *Psychometrika*, vol. 30, '
        "no. 2, pp. 179–185, Jun. 1965, doi: 10.1007/BF02289447.",
        "Parallel analysis.",
        "Parallel-analysis retention diagnostic.",
        "Crossref DOI record."),
    "rousseeuw1987": (
        'P. J. Rousseeuw, "Silhouettes: A graphical aid to the interpretation and validation of cluster analysis," '
        "*J. Comput. Appl. Math.*, vol. 20, pp. 53–65, Nov. 1987, doi: 10.1016/0377-0427(87)90125-7.",
        "Silhouette coefficient.",
        "Cluster separation diagnostic.",
        "Crossref DOI record."),
}
