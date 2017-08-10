/*
 * cutility.h
 *
 *  Created on: 2015. 11. 19.
 *      Author: user
 */

#ifndef CUTILITY_H_
#define CUTILITY_H_

#include <stdio.h>
#include <stdarg.h>

// 모든 문자열 함수는 마지막 0를 보장한다.
// 안정성을 위하여 size는 버퍼 크기로 간주하고 문자열은 최대 size-1안에서 처리한다.
// 호출시 버퍼크기임을 항상 염두에 둘 것,

void c_strtrim (char *str, int size);		// both side
void c_strltrim(char *str, int size);		// left side
void c_strrtrim(char *str, int size);		// right side

char* c_strcpy(char *dest, char *src, int size);
int   c_strcmp(char *s1, char *s2, int max, int both_null);	// if s1 and s2 is NULL, return both_null
int   c_strlen(char *str, int max);								// if NULL return 0, if big, return max

int   c_strmatch(char *s1, char *s2);
int   c_strimatch(char *s1, char *s2);

char* c_strdup(char *src, int max);

char*	c_strchr (char *src, int ch, int size);		// if not found, return NULL
char*	c_strrchr(char *src, int ch, int size);		// if not found, return NULL

char*	c_strstr (char *src, char* str, int size);		// if not found, return NULL
char*	c_strrstr(char *src, char* str, int size);		// if not found, return NULL

void	c_strcat (char *dest, char* src, int size);

void 	c_memset(void *buf,  int ch,     int len);
void*	c_memcpy(void *dest, void* src,  int len);
int 	c_memcmp(void *buf1, void* buf2, int len, int ret_both_null);

char*	c_alloc (int size);		// set by 0
void  c_free  (char **ptr);

int	c_get_number(char *str, int size,  int* value);  						// return : used_length
int	c_get_word  (char *buf, int bsize, char* delemeter, char* word, int wsize);  // return : used_length

#endif /* CUTILITY_H_ */
