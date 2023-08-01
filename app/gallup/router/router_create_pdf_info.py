from typing import Any

from fastapi import Depends, HTTPException, UploadFile, Response, File, Form
from pydantic import Field

from app.auth.adapters.jwt_service import JWTData
from app.auth.router.dependencies import parse_jwt_user_data
from app.utils import AppModel

from ..service import Service, get_service
from . import router
import pandas as pd
import logging
import numpy as np
import PyPDF2
import re
import os
from io import BytesIO

from typing import Any, List
from fastapi import Depends, HTTPException, UploadFile


# class CreatePDFRequest(AppModel):
# date_of_test: str


class CreatePDFResponse(AppModel):
    id: Any = Field(alias="_id")


@router.post("/pdf", response_model=CreatePDFResponse)
def create_info(
    file: UploadFile = File(...),
    input: str = Form(...),
    MBTI: str = Form(...),
    MIT: str = Form(...),
    jwt_data: JWTData = Depends(parse_jwt_user_data),
    svc: Service = Depends(get_service),
) -> Any:
    user_id = jwt_data.user_id
    pdf_content = extract_text(file.file)
    logging.info(pdf_content)

    Nurs_data = strengths_list_generator(pdf_content, 35)
    logging.info(Nurs_data)
    if len(Nurs_data) == 0:
        raise HTTPException(status_code=500, detail=f"Wrong file was uploaded")
    Nurs_df = pd.DataFrame([np.arange(1, 35).tolist()], columns=Nurs_data)
    Nurs_df = Nurs_df.reindex(sorted(Nurs_df.columns), axis=1)
    csv_buffer = BytesIO()
    Nurs_df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    filename, _ = os.path.splitext(file.filename)
    csv_filename = f"{filename}.csv"
    url = svc.s3_service.upload_file(csv_buffer, csv_filename)
    url = url.replace(" ", "+")
    payload = {}
    payload["date"] = input
    payload["MBTI"] = MBTI
    payload["url"] = url
    payload["MIT"] = MIT
    payload["tokens_used"] = 0
    payload["chat_hsitory"] = ""
    inserted_id = svc.repository.create_pdf(user_id=user_id, payload=payload)
    return CreatePDFResponse(id=inserted_id)


@router.get("/{pdf_id:str}/pdf_similarity")
def get_pdf_similarity(
    pdf_id: str,
    jwt_data: JWTData = Depends(parse_jwt_user_data),
    svc: Service = Depends(get_service),
) -> Any:
    pdf_url = svc.repository.get_pdf_url(pdf_id=pdf_id, user_id=jwt_data.user_id)
    if pdf_url.get("pdf_similarities"):
        table_data = pd.read_csv(pdf_url.get("pdf_similarities")).to_dict(orient="records")
        return table_data
    pdf_url = pdf_url.get("url")
    df = pd.read_csv(
        "https://galluppublic.s3.eu-north-1.amazonaws.com/posts/Professions+v1.0+-+test.csv"
    )
    df = df.drop(columns=["IsGood MIT", "IsGood 34"])
    df = df.reindex(sorted(df.columns), axis=1)
    Nurs_df = pd.read_csv(pdf_url)

    x = np.arange(1, 35)
    y = []
    for i in range(34):
        y.append(1 / (1 + np.exp(-(17 - x[i]) / np.pi)))

    x_2 = np.arange(1, 18)
    y_2 = []
    for i in range(17):
        y_2.append(1 / (1 + np.exp(-(17 / 2 - x_2[i]) / (np.pi / 2))))

    z = np.arange(1, 35)
    error = []
    for i in range(17):
        error.append(abs(z[i] - z[-(i + 1)]) * y_2[i])
    Max_error = sum(error) * 2
    logging.info(Max_error)

    professions = []
    for j in range(len(df.iloc[:, 0])):
        Total_num = 0
        for i in range(33):
            if df.iloc[j, i]:
                Total_num += (
                    abs(df.iloc[j, i] - Nurs_df.iloc[0, i]) * y[df.iloc[j, i] - 1]
                )

        professions.append(round((Max_error - Total_num) * 100 / (Max_error * 0.95), 2))

    list_pro = []
    for pro in df["Специализация"]:
        list_pro.append(pro)

    list_field = []
    for pro in df['Сфера']:
        list_field.append(pro)

    list_sub_field = []
    for pro in df["Сфера деятельности"]:
        list_sub_field.append(pro)
    
    list_numb = list(range(1, (len(list_pro)) + 1))

    Full_list = pd.DataFrame({
     'Field': list_field,
     'Subfield': list_sub_field,
     'Professions': list_pro,
     'Percentage fitting': professions
     
    })
    Full_list = Full_list.sort_values(by='Percentage fitting', ascending=False)
    Full_list.insert(0, 'Place', list_numb) 
    csv_buffer = BytesIO()
    Full_list.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    csv_filename = f"{pdf_id}_similaties.csv"
    url = svc.s3_service.upload_file(csv_buffer, csv_filename)
    url = url.replace(" ", "+")
    table_data = pd.read_csv(url).to_dict(orient="records")
    if Full_list is None:
        raise HTTPException(status_code=500, detail=f"File {csv_filename} not uploaded")

    update_result = svc.repository.update_pdf_by_id(
        pdf_id=pdf_id, user_id=jwt_data.user_id, data={"pdf_similarities": url}
    )
    if update_result.acknowledged:
        return table_data
    raise HTTPException(
        status_code=404, detail=f"Error occured while updating shanyrak {pdf_id}"
    )


@router.get("/{pdf_id:str}/pdf_comments")
def get_pdf_comments(
    pdf_id: str,
    jwt_data: JWTData = Depends(parse_jwt_user_data),
    svc: Service = Depends(get_service),
) -> Any:
    pdf_url = svc.repository.get_pdf_url(pdf_id=pdf_id, user_id=jwt_data.user_id)
    if pdf_url.get("pdf_comment"):
        comments = pdf_url.get("pdf_comment")
        logging.info(comments)
        index = comments.find("galluppublic/")
        file_name = pdf_url.get("pdf_comment")[index + len('galluppublic/'):]
        content_str = svc.s3_service.get_file_string(file_name)
        return content_str
    pdf_url_main = pdf_url.get("url")
    df = pd.read_csv(pdf_url_main, header=None)
    transposed_df = df.transpose()
    reset_df = transposed_df.reset_index()
    reset_df = reset_df.drop(reset_df.columns[0], axis=1)
    reset_df.columns = ["name", "value"]
    sorted_df = reset_df.sort_values(by="value")
    df_list = sorted_df[["value", "name"]].values.tolist()
    str_list = [" ".join(i) for i in df_list]
    sorted_list = sorted(str_list, key=lambda s: int(s.split()[0]))
    first_15 = sorted_list[:15]
    str_result = ", ".join(first_15)
    svc.repository.update_pdf_by_id(
        pdf_id=pdf_id, user_id=jwt_data.user_id, data={"best_themes": str_result}
    )
    pdf_sim_url = pdf_url.get("pdf_similarities")
    df_prof = pd.read_csv(pdf_sim_url)
    df_prof = df_prof.iloc[0:5, 2].tolist()
    srt_prof = ", ".join(str(x) for x in df_prof)
    MBTI_str = pdf_url.get("MBTI")
    MIT_str = pdf_url.get("MIT")
    personality, career_fields, profession = svc.OpenAI_service.professions_list(str_result, srt_prof, MBTI_str, MIT_str)
    combined_str = "REPORT 1: EXPLORE YOUR PERSONALITY\n" + personality + "\n\n REPORT 2: BEST CAREER FIELDS" + career_fields + "\n\n REPORT 3: TOP 5 PROFESSIONS" + profession
    txt_filename = f"txt_files/{pdf_id}_comments.txt"
    with open(txt_filename, "w") as text_file:
        text_file.write(combined_str)
    url = svc.s3_service.upload_file_path(txt_filename, txt_filename)
    url = url.replace(" ", "+")

    update_result = svc.repository.update_pdf_by_id(
        pdf_id=pdf_id, user_id=jwt_data.user_id, data={"pdf_comment": url}
    )
    if update_result.acknowledged:
        return combined_str
    raise HTTPException(
        status_code=404, detail=f"Error occured while updating pdf {pdf_id}"
    )


# functions


def extract_text(file) -> str:
    reader = PyPDF2.PdfReader(file)
    page = reader.pages[0]
    text = page.extract_text()
    return text


def extract_strings_between(text, start_string, end_string):
    pattern = r"{}(.*?){}".format(re.escape(start_string), re.escape(end_string))
    matches = re.findall(pattern, text, re.DOTALL)
    return matches


def numerate_list_elements(lst):
    cleaned_list = [element.replace(" ", "") for element in lst]
    navigate_droped_list = [element.replace("NAVIGATE", "") for element in cleaned_list]

    return navigate_droped_list


def strengths_list_generator(text, number):
    list_of_strengths = []
    for i in range(number):
        if i < 34:
            list_of_strengths.extend(
                extract_strings_between(text, f"\n{i}.", f"\n{i+1}.")
            )
        elif i == 34:
            list_of_strengths.extend(extract_strings_between(text, f"\n{i}.", "You"))
        else:
            pass

    return numerate_list_elements(list_of_strengths)
