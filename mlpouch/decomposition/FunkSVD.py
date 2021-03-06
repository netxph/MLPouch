from sklearn.base import BaseEstimator, TransformerMixin
from mlpouch import BaseRecommender
import logging
import numpy as np
import pandas as pd

class FunkSVD(TransformerMixin, BaseEstimator, BaseRecommender):
    
    def __init__(self, latent_features = 4, learning_rate = 0.0001, iters = 100):
        self.latent_features = latent_features
        self.learning_rate = learning_rate
        self.iters = iters

    def fit(self, X, y = None):

        X_matrix = self.fit_transform(X, y)

        X_transformed = pd.DataFrame(X_matrix)
        X_transformed[self.U_index.name] = self.U_index.array
        X_transformed = X_transformed.set_index(self.U_index.name)
        X_transformed.columns = self.VT_index

        self.X_transformed = X_transformed

        return self

    def fit_transform(self, X, y = None):

        self.U_index = X.index
        self.VT_index = X.columns

        # Convert to matrix
        X = np.matrix(X)
    
        # Set up useful values to be used through the rest of the function
        n_U = X.shape[0]
        n_VT = X.shape[1]
        with_values = np.count_nonzero(~np.isnan(X))

        # initialize the user and movie matrices with random values
        U_matrix = np.random.rand(n_U, self.latent_features)
        VT_matrix = np.random.rand(self.latent_features, n_VT)
    
        # initialize sse at 0 for first iteration
        sse_accum = 0
    
        # keep track of iteration and MSE
        logging.debug("Optimization Statistics")
        logging.debug("Iterations | Mean Squared Error ")
    
        # for each iteration
        for iteration in range(self.iters):

            # update our sse
            old_sse = sse_accum
            sse_accum = 0
            
            # For each user-movie pair
            for i in range(n_U):
                for j in range(n_VT):
                    
                    # if the rating exists
                    if X[i, j] > 0:
                        
                        # compute the error as the actual minus the dot product of the user and movie latent features
                        diff = X[i, j] - np.dot(U_matrix[i, :], VT_matrix[:, j])
                        
                        # Keep track of the sum of squared errors for the matrix
                        sse_accum += diff**2
                        
                        # update the values in each matrix in the direction of the gradient
                        for k in range(self.latent_features):
                            U_matrix[i, k] += self.learning_rate * (2 * diff * VT_matrix[k, j])
                            VT_matrix[k, j] += self.learning_rate * (2 * diff * U_matrix[i, k])

            self.sse_score = sse_accum / with_values

            # print results
            logging.debug(f"{iteration + 1} \t\t {self.sse_score}")
            
        self.U_matrix = U_matrix
        self.VT_matrix = VT_matrix

        X_matrix = np.dot(self.U_matrix, self.VT_matrix)


        return X_matrix

    def recommend(self, U, rec_num = 5):
        recommends = []

        for U_item in U:
            recommends.append([ U_item, self._recommend(U_item, rec_num) ])

        return recommends

    def _recommend(self, U_item, rec_num = 5):
        return self.X_transformed.loc[U_item] \
            .sort_values(ascending = False) \
            .head(rec_num) \
            .index.tolist()
