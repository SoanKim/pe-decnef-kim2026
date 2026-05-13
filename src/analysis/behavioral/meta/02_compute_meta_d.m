% Title: Maximum Likelihood Estimation of Meta-d'
% Project: pe-decnef-kim2026
% Author: Soan Kim
% Purpose: Compute metacognitive sensitivity using the Maniscalco and Lau algorithm, applying 0.25 padding to input arrays to prevent log(0) optimization crashes.


data = readtable('/[put dir here]/matlab_meta_d_input.csv'); % Load the R data
results = zeros(height(data), 1);

%{
Column 4: err_4 (Incorrect trial, Confidence 4 - High)
Column 5: err_3 (Incorrect trial, Confidence 3)
Column 6: err_2 (Incorrect trial, Confidence 2)
Column 7: err_1 (Incorrect trial, Confidence 1 - Low)
Column 8: corr_1 (Correct trial, Confidence 1 - Low)
Column 9: corr_2 (Correct trial, Confidence 2)
Column 10: corr_3 (Correct trial, Confidence 3)
Column 11: corr_4 (Correct trial, Confidence 4 - High)
%}

for i = 1:height(data)
    nR_S1 = table2array(data(i, 4:11));
    nR_S2 = table2array(data(i, [11, 10, 9, 8, 7, 6, 5, 4]));
    
    nR_S1 = nR_S1 + 0.25;  % to prevent log(0) empty bin crashes
    nR_S2 = nR_S2 + 0.25;
    
    try
        fit = fit_meta_d_MLE(nR_S1, nR_S2);
        results(i) = fit.meta_d;
    catch e
        warning('Failed on row %d: %s', i, e.message);
        results(i) = NaN;
    end
end

data.meta_d = results;
data.m_ratio = data.meta_d ./ data.d_prime_4afc;

writetable(data, 'matlab_meta_d_output.csv');
disp('Successfully finished! File saved as matlab_meta_d_output.csv');
