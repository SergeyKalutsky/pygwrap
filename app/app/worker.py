import os
import pandas as pd
from app.core.celery_app import celery_app


def market_segment_sheet(orig_df, price_group,
                         expence_coef, exchange_rate,
                         factory_price_col, factory_num_col,
                         market_price_col):

    df = orig_df.copy()
    for num in df[factory_num_col].unique():
        temp = df[df[factory_num_col] == num]
        top = int(temp.shape[0]*price_group/100)

        # discount mean price
        price_mean_top = temp[:top][market_price_col].mean()
        price_mean_top_factory = price_mean_top / expence_coef / exchange_rate
        discount = 1 - price_mean_top_factory / \
            temp[factory_price_col].values[0]

        # discount threshold_price
        threshold_top = float(temp[:top][market_price_col].max())
        price_mean_threshold_factory = threshold_top/expence_coef/exchange_rate
        discount_threshold = 1 - price_mean_threshold_factory / \
            temp[factory_price_col].values[0]

        # calculate final values for excel sheet
        in_top = 1 if (
            float(temp['Цена_cworks'].values[0]) < threshold_top) else 0
        df.loc[temp.index, f'Kол-во_{price_group}%'] = top
        df.loc[temp.index, f'Порог_вхождения_{price_group}%'] = threshold_top
        df.loc[temp.index, f'Проходим_в_{price_group}%'] = in_top
        df.loc[temp.index, f'Скидка_ср_цена{price_group}%'] = discount
        df.loc[temp.index, f'Скидка_порог_{price_group}%'] = discount_threshold
    return df


def calc_place(temp, cworks_price, market_price_col):
    for place, price in enumerate(temp[market_price_col]):
        if cworks_price < price:
            return place
    return 0


def placement(start_df, factory_num_col, market_price_col):
    df = start_df.copy()
    places_dict = {}
    for num in df[factory_num_col].unique():
        temp = df[df[factory_num_col] == num]
        length = len(temp)
        cworks_price = temp['Цена_cworks'].unique()[0]
        place = calc_place(temp, cworks_price, market_price_col)
        places_dict[num] = (place/length)

    return places_dict


def write_excel(save_path, price_groups, df_lst, stat):
    writer = pd.ExcelWriter(save_path, engine='xlsxwriter')
    for df, group in zip(df_lst, price_groups):
        df.to_excel(writer, sheet_name=f'доля_рынка{group}%', index=False)
    stat.to_excel(writer, sheet_name='итог', index=False)
    writer.save()


@celery_app.task(acks_late=True)
def market_eval(filepath, expences_coef, market_price_col,
                factory_price_col, factory_num_col, exchange_rate):

    mapping = {
        4: '30%',
        3: '40%',
        2: '50%',
        1: '60%',
        0: '>60%'
    }

    expences_coef = float(expences_coef)
    exchange_rate = float(exchange_rate)

    data = pd.read_excel(filepath)
    data['Цена_cworks'] = data[factory_price_col] * \
        expences_coef * exchange_rate

    df_lst = []
    stat_df = pd.DataFrame()
    price_groups = [30, 40, 50, 60]
    for price_group in price_groups:
        df = market_segment_sheet(data, price_group,
                                  expences_coef, exchange_rate,
                                  factory_price_col, factory_num_col,
                                  market_price_col)
        df_lst.append(df)
        df = df[df.columns[:3].to_list() + df.columns[-3:].to_list()]
        df = df.drop_duplicates()
        if stat_df.empty:
            stat_df = df
        else:
            stat_df = pd.concat([stat_df, df[df.columns[3:]]], axis=1)

    stat_df.fillna(0, inplace=True)
    cols = [col for col in stat_df.columns if 'Проходим_в_' in col]
    stat_df['Сегмент_рынка'] = stat_df[cols].sum(axis=1).map(mapping)
    stat_df.drop(columns=cols, inplace=True)
    stat_df['Относительное_положение'] = stat_df[factory_num_col].map(
        placement(data, factory_num_col, market_price_col))

    save_path = os.path.join(os.path.dirname(filepath), 'result.xlsx')
    write_excel(save_path, price_groups,  df_lst, stat_df)
