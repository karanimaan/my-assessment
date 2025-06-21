"""
The database loan.db consists of 5 tables:
   1. customers - table containing customer data
   2. loans - table containing loan data pertaining to customers
   3. credit - table containing credit and creditscore data pertaining to customers
   4. repayments - table containing loan repayment data pertaining to customers
   5. months - table containing month name and month ID data

You are required to make use of your knowledge in SQL to query the database object (saved as loan.db) and return the requested information.
Simply fill in the vacant space wrapped in triple quotes per question (each function represents a question)

NOTE:
The database will be reset when grading each section. Any changes made to the database in the previous `SQL` section can be ignored.
Each question in this section is isolated unless it is stated that questions are linked.
Remember to clean your data

"""


def question_1():
    """
    Make use of a JOIN to find the `AverageIncome` per `CustomerClass`
    """

    qry = """
        SELECT CustomerClass, SUM(Income)/Count(*) as AverageIncome
        FROM (SELECT DISTINCT * FROM credit LEFT JOIN customers ON credit.CustomerID = customers.CustomerID)
        GROUP BY CustomerClass
    """
    # Left join is used here on CustomerID. Any join can be used because CustomerID column is identical in both tables.
    # There are a few duplicates in each table (of the same CustomerID).DISTINCT removes them.
    # Resultant joined table is 1000 rows long with CustomerID and primary key.
    # This joined table is grouped by CustomerClass, and AverageIncome is calculated as the sum of each group's
    # customer's income divided by the number of customers in the group.
    return qry


def question_2():
    """
    Make use of a JOIN to return a breakdown of the number of 'RejectedApplications' per 'Province'.
    Ensure consistent use of either the abbreviated or full version of each province, matching the format found in the customer table.
    """

    qry = """
        SELECT 
                CASE Region
                    WHEN 'GT' THEN 'Gauteng'
                    WHEN 'EC' THEN 'EasternCape'
                    WHEN 'FS' THEN 'FreeState'
                    WHEN 'KZN' THEN 'KwaZulu-Natal'
                    WHEN 'LP' THEN 'Limpopo'
                    WHEN 'MP' THEN 'Mpumalanga'
                    WHEN 'NC' THEN 'NorthernCape'
                    WHEN 'NW' THEN 'NorthWest'
                    WHEN 'WC' THEN 'WesternCape'
                    ELSE Region  /* if not the above abbreviations, then it is already in full form */
                END 
            AS Province,
            SUM(CASE WHEN ApprovalStatus = 'Rejected' THEN 1 ELSE 0 END) AS RejectedApplications
        FROM (SELECT DISTINCT * FROM customers LEFT JOIN loans ON customers.CustomerID = loans.CustomerID)
        GROUP BY Province
    """

    return qry


def question_3():
    """
    Making use of the `INSERT` function, create a new table called `financing` which will include the following columns:
    `CustomerID`,`Income`,`LoanAmount`,`LoanTerm`,`InterestRate`,`ApprovalStatus` and `CreditScore`

    Do not return the new table, just create it.
    """

    qry = """
        -- recreate `financing` table
        DROP TABLE IF EXISTS financing;
        CREATE TABLE financing (
            CustomerID int,
            Income int,
            LoanAmount int,
            LoanTerm int,
            InterestRate float,
            ApprovalStatus varchar,
            CreditScore int
        );
        
        INSERT INTO financing
            SELECT DISTINCT CustomerID, Income, LoanAmount, LoanTerm, InterestRate, ApprovalStatus, CreditScore
            FROM customers NATURAL JOIN loans NATURAL JOIN credit   -- Natural Join is an Inner Join with an implicit On clause. Again, selection of Join is arbitrary.
    """

    return qry


# Question 4 and 5 are linked


def question_4():
    """
    Using a `CROSS JOIN` and the `months` table, create a new table called `timeline` that sumarises Repayments per customer per month.
    Columns should be: `CustomerID`, `MonthName`, `NumberOfRepayments`, `AmountTotal`.
    Repayments should only occur between 6am and 6pm London Time.
    Null values to be filled with 0.

    Hint: there should be 12x CustomerID = 1.
    """

    qry = """
        DROP TABLE IF EXISTS timeline;
        CREATE TABLE timeline (
            CustomerID int,
            MonthName varchar,
            NumberOfRepayments int,
            AmountTotal double
        );
        -- Primary key is (CustomerID, MonthName)
        INSERT INTO timeline
            SELECT 
                CustomerID, 
                MonthName,
                
                /* NumberOfRepayments */
                SUM(CASE WHEN ( 
                    MonthID = CAST(month(RepaymentDate) AS int)     -- check if MonthID == month in Repayment date
                    AND 
                        -- if RepaymentDate hour (in London time) is within the 6am to 6pm
                        (
                            hour(RepaymentDate) 
                            + 
                            CASE TimeZone
                                WHEN 'PST' THEN -8
                                WHEN 'IST' THEN 5.5
                                WHEN 'JST' THEN 9
                                WHEN 'EET' THEN 2
                                WHEN 'PNT' THEN -7
                                WHEN 'CST' THEN -6
                                WHEN 'GMT' THEN 0
                                WHEN 'CET' THEN 1
                                WHEN 'UTC' THEN 0
                                ELSE NULL
                            END
                            + 1     /* London is in GMT+1 */
                        ) BETWEEN 6 AND 17
                ) THEN 1 ELSE 0 END),   -- if both conditions are true, then count repayment for (CustomerID, MonthName)
    
                /* AmountTotal */
                SUM(CASE WHEN ( 
                    MonthID = CAST(month(RepaymentDate) AS int) 
                    AND 
                        (
                            hour(RepaymentDate) 
                            + 
                            CASE TimeZone
                                WHEN 'PST' THEN -8
                                WHEN 'IST' THEN 5.5
                                WHEN 'JST' THEN 9
                                WHEN 'EET' THEN 2
                                WHEN 'PNT' THEN -7
                                WHEN 'CST' THEN -6
                                WHEN 'GMT' THEN 0
                                WHEN 'CET' THEN 1
                                WHEN 'UTC' THEN 0
                                ELSE NULL
                            END
                            + 1     /* London is in GMT+1 */
                        ) BETWEEN 6 AND 17
                ) THEN Amount ELSE 0 END)   -- if both conditions are true, then add repayment to total for (CustomerID, MonthName)
                
            FROM (SELECT * FROM customers LEFT JOIN repayments ON customers.CustomerID = repayments.CustomerID) -- this adds customers who have not made any repayments at all
                CROSS JOIN months   -- every `customers-repayments` record is multiplied 12 times for each month of the year
            GROUP BY CustomerID, MonthName
    """

    return qry


def question_5():
    """
    Make use of conditional aggregation to pivot the `timeline` table such that the columns are as follows:
    `CustomerID`, `JanuaryRepayments`, `JanuaryTotal`,...,`DecemberRepayments`, `DecemberTotal`,...etc
    MonthRepayments columns (e.g JanuaryRepayments) should be integers

    Hint: there should be 1x CustomerID = 1
    """

    qry = """
    WITH pivoted_timeline AS (
        SELECT *
        FROM timeline
        PIVOT (
            -- show aggregate columns for "repayments and total of each month" for each cusomter
            -- However, aggregation is applied on one value, not multiple (no actual aggregation is happening, the table is just being partially flattened).
            -- `first` is used since explicit aggregate expression is expected
            first(NumberOfRepayments) AS Repayments,
            first(AmountTotal) AS Total
            FOR MonthName IN ('January', 'February', 'March', 'April', 'May', 'June',
                              'July', 'August', 'September', 'October', 'November', 'December')
        )
    )
    SELECT
        CustomerID,
        January_Repayments AS JanuaryRepayments,
        January_Total AS JanuaryTotal,
        February_Repayments AS FebruaryRepayments,
        February_Total AS FebruaryTotal,
        March_Repayments AS MarchRepayments,
        March_Total AS MarchTotal,
        April_Repayments AS AprilRepayments,
        April_Total AS AprilTotal,
        May_Repayments AS MayRepayments,
        May_Total AS MayTotal,
        June_Repayments AS JuneRepayments,
        June_Total AS JuneTotal,
        July_Repayments AS JulyRepayments,
        July_Total AS JulyTotal,
        August_Repayments AS AugustRepayments,
        August_Total AS AugustTotal,
        September_Repayments AS SeptemberRepayments,
        September_Total AS SeptemberTotal,
        October_Repayments AS OctoberRepayments,
        October_Total AS OctoberTotal,
        November_Repayments AS NovemberRepayments,
        November_Total AS NovemberTotal,
        December_Repayments AS DecemberRepayments,
        December_Total AS DecemberTotal
    FROM pivoted_timeline;

    """
    # Pivoted timeline table shows all 1000 CustomerIDs each having a row showing the number of repayments and total for each month

    return qry


# QUESTION 6 and 7 are linked, Do not be concerned with timezones or repayment times for these question.


def question_6():
    """
    The `customers` table was created by merging two separate tables: one containing data for male customers and the other for female customers.
    Due to an error, the data in the age columns were misaligned in both original tables, resulting in a shift of two places upwards in
    relation to the corresponding CustomerID.

    Create a table called `corrected_customers` with columns: `CustomerID`, `Age`, `CorrectedAge`, `Gender`
    Utilize a window function to correct this mistake in the new `CorrectedAge` column.
    Null values can be input manually - i.e. values that overflow should loop to the top of each gender.

    Also return a result set for this table (ie SELECT * FROM corrected_customers)
    """

    qry = """
        DROP TABLE IF EXISTS corrected_customers;
        CREATE TABLE corrected_customers (
            CustomerID int,
            Age int,
            CorrectedAge int,
            Gender varchar
        );
        
        INSERT INTO corrected_customers
        
            -- This solution is better for the case if the misalignment was large because the null values are not input manually
            WITH 
                -- Indexed table is customers table that is numbered according to order of Gender then CustomerID
                indexed AS (
                    SELECT *,
                           ROW_NUMBER() OVER (PARTITION BY Gender ORDER BY CustomerID) AS RowNumber,   -- Row number ordered by Gender and CustomerID
                           COUNT(*) OVER (PARTITION BY Gender) AS GenderTotal     -- Total customers per Gender
                    FROM (SELECT DISTINCT * FROM customers)     -- Removes duplicate records
                )
            -- Join Indexed table with lagged copy of itself. They are joined on Gender and RowNumber lagged by 2 (and wrapped)
            SELECT
                original.CustomerID,
                original.Age,
                lagged.Age AS CorrectedAge,
                original.Gender
            FROM 
                indexed AS original
                LEFT JOIN indexed AS lagged
                ON 
                    original.Gender = lagged.Gender
                    AND 
                    -- Lagged RowNumber must be (Original RowNumber - 2) or (Original last row number of gender - 2 + Original RowNumber)
                    lagged.RowNumber = 
                        CASE
                            WHEN original.RowNumber > 2 THEN original.RowNumber - 2
                            ELSE original.GenderTotal - 2 + original.RowNumber 
                        END
            ;
            
            SELECT * FROM corrected_customers

    """

    return qry


def question_7():
    """
    Create a column in corrected_customers called 'AgeCategory' that categorizes customers by age.
    Age categories should be as follows:
        - `Teen`: CorrectedAge < 20
        - `Young Adult`: 20 <= CorrectedAge < 30
        - `Adult`: 30 <= CorrectedAge < 60
        - `Pensioner`: CorrectedAge >= 60

    Make use of a windows function to assign a rank to each customer based on the total number of repayments per age group. Add this into a "Rank" column.
    The ranking should not skip numbers in the sequence, even when there are ties, i.e. 1,2,2,2,3,4 not 1,2,2,2,5,6
    Customers with no repayments should be included as 0 in the result.

    Return columns: `CustomerID`, `Age`, `CorrectedAge`, `Gender`, `AgeCategory`, `Rank`
    """

    qry = """
    -- Recreate AgeCategory Column
    ALTER TABLE corrected_customers
    ADD IF NOT EXISTS AgeCategory VARCHAR;
    
    -- Populate AgeCategory Column
    UPDATE corrected_customers
    SET AgeCategory = CASE
        WHEN CorrectedAge < 20 THEN 'Teen'
        WHEN CorrectedAge BETWEEN 20 AND 29 THEN 'Young Adult'
        WHEN CorrectedAge BETWEEN 30 AND 59 THEN 'Adult'
        WHEN CorrectedAge >= 60 THEN 'Pensioner'
    END;
    
    -- Add Rank column, which ranks each customer in his age group, based on his total number of repayments 
    WITH 
        customers_repayments AS (
            SELECT 
                CustomerID, Age, CorrectedAge, Gender, AgeCategory,
                COUNT(RepaymentID) OVER (PARTITION BY CustomerID) AS TotalRepaymentsPerCustomer
                    -- Counts the number of repayments associated
            FROM corrected_customers NATURAL LEFT JOIN repayments   
                -- Combined table of corrected_customers and repayments, showing each customer with each of his repayments. 
                -- Customers without repayments are included with null for the repayments fields
    )
    SELECT 
        CustomerID, Age, CorrectedAge, Gender, AgeCategory,
        DENSE_RANK() OVER (PARTITION BY AgeCategory ORDER BY TotalRepaymentsPerCustomer) AS Rank
            -- Dense Rank does not skip numbers. Ranks each customer within his age group based on his total repayments
    FROM customers_repayments
    """

    return qry
