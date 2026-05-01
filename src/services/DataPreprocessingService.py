import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

class DataPreprocessingService:
    def __init__(self):
        pass
    
    def load_folder(self, path: str) -> pd.DataFrame:
        df_list = []

        for filename in os.listdir(path):
            if filename.endswith(".csv"):
                full_path = os.path.join(path, filename)
                df = self.load(full_path)
                if df is not None:
                    df_list.append(df)

        if not df_list:
            raise ValueError("No CSV files found")

        df = pd.concat(df_list, ignore_index=True)

        print(f"Loaded {len(df_list)} files, total rows: {len(df)}")
        return df

    def load(self, path):
        if not os.path.exists(path):
            print("File not found")
            return
        df = pd.read_csv(path)
        print("Data loaded successfully")
        print(df.head())
        return df
        
    def clean(self, df: pd.DataFrame):
        
        print("Cleaning data")
        
        # Xử lý missing value
        # self.df.isna().sum() # -> cột merch_zipcode bị thiếu, nhưng đã có merch_lat, merch_long rồi nên có thể drop luôn
        # zip, merch_zipcode là categorical
        df.drop("merch_zipcode", axis=1, inplace=True)
        df.drop("zip", axis=1, inplace=True) # Tương tự drop zip vì ko cần thiết
        # =========================
        if "trans_num" in df.columns:
            before = len(df)
            df.drop_duplicates(subset=["trans_num"], inplace=True)
            print(f"Removed {before - len(df)} duplicates (by trans_num)")
        else:
            df.drop_duplicates(inplace=True)
            
        # =========================
        # self.df.isna().sum()
        # self.df.isnull().sum()
        
        
        drop_columns = ["Unnamed: 0", "cc_num", "trans_num", "first", "last", "street", "city", "state"]
        df.drop(columns=drop_columns, inplace=True)
        
        df["merchant"] = df["merchant"].str.replace("fraud_", "")
        
        df["trans_date_trans_time"] = pd.to_datetime(df["trans_date_trans_time"])
        df['hour'] = df['trans_date_trans_time'].dt.hour
        df['day_of_week'] = df['trans_date_trans_time'].dt.dayofweek
        df.drop("trans_date_trans_time", axis=1, inplace=True)
        df.drop("unix_time", axis=1, inplace=True) # drop unix time vì trùng dữ liệu

        # Xử lý dob -> age
        df['dob'] = pd.to_datetime(df['dob'])
        df['age'] = (pd.Timestamp.now() - df['dob']).dt.days // 365
        df = df.drop(columns=['dob'])

        # Thêm distance
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371
            dlat = np.radians(lat2 - lat1)
            dlon = np.radians(lon2 - lon1)

            a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
            c = 2 * np.arcsin(np.sqrt(a))

            return R * c

        df['distance'] = haversine(
            df['lat'], df['long'], df['merch_lat'], df['merch_long']
        )
        
        return df
        
    def prepare(self, filePath: str) -> pd.DataFrame:
        df = self.load(filePath)
        df = self.clean(df)
        return df

        